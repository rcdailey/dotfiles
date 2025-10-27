"""
MS Teams Cache Parser

Parses IndexedDB data from local Teams cache to extract conversations,
messages, participants, and call logs.
"""

import platform
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import html2text

from ccl_chrome_indexeddb import ccl_chromium_indexeddb, ccl_leveldb
from ccl_chrome_indexeddb import ccl_blink_value_deserializer, ccl_v8_value_deserializer
import io


class TeamsCache:
    """Parser for MS Teams cache data"""

    def __init__(self, cache_path: Optional[str] = None):
        self.cache_path = cache_path or self._detect_teams_cache()
        self._data = None
        self._user_map = {}
        self._conversations = {}
        self._messages = {}
        self.h2t = html2text.HTML2Text()
        self.h2t.images_to_alt = True
        self.h2t.body_width = 0

    def _detect_teams_cache(self) -> str:
        """Auto-detect Teams cache location based on platform"""
        system = platform.system()
        home = Path.home()

        if system == "Darwin":  # macOS
            paths = [
                home
                / "Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/EBWebView/WV2Profile_tfw/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb",
                home
                / "Library/Application Support/Microsoft/Teams/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb",
            ]
        elif system == "Windows":
            paths = [
                home
                / "AppData/Local/Packages/MicrosoftTeams_8wekyb3d8bbwe/LocalCache/Microsoft/MSTeams/EBWebView/Default/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb",
                home
                / "AppData/Roaming/Microsoft/Teams/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb",
            ]
        elif system == "Linux":
            paths = [
                home
                / ".config/Microsoft/Microsoft Teams/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb"
            ]
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

        for path in paths:
            if path.exists():
                return str(path)

        raise FileNotFoundError(
            "Teams cache not found. Is Teams installed? "
            f"Searched paths: {[str(p) for p in paths]}"
        )

    def _parse_indexeddb(self):
        """Parse the IndexedDB LevelDB database"""
        if self._data is not None:
            return  # Already parsed

        db = ccl_leveldb.RawLevelDb(self.cache_path)
        fetched_records = list(db.iterate_records_raw())

        # Parse metadata
        global_metadata_raw = {}
        for record in fetched_records:
            if (
                record.key.startswith(b"\x00\x00\x00\x00")
                and record.state == ccl_leveldb.KeyState.Live
            ):
                if (
                    record.key not in global_metadata_raw
                    or global_metadata_raw[record.key].seq < record.seq
                ):
                    global_metadata_raw[record.key] = record

        global_metadata = ccl_chromium_indexeddb.GlobalMetadata(global_metadata_raw)

        # Extract database and object store metadata
        database_metadata_raw = {}
        objectstore_metadata_raw = {}

        for db_id in global_metadata.db_ids:
            if db_id.dbid_no > 0x7F:
                continue

            prefix_database = bytes([0, db_id.dbid_no, 0, 0])
            prefix_objectstore = bytes([0, db_id.dbid_no, 0, 0, 50])

            for record in reversed(fetched_records):
                if (
                    record.key.startswith(prefix_database)
                    and record.state == ccl_leveldb.KeyState.Live
                ):
                    meta_type = record.key[len(prefix_database)]
                    old_version = database_metadata_raw.get((db_id.dbid_no, meta_type))
                    if old_version is None or old_version.seq < record.seq:
                        database_metadata_raw[(db_id.dbid_no, meta_type)] = record

                if (
                    record.key.startswith(prefix_objectstore)
                    and record.state == ccl_leveldb.KeyState.Live
                ):
                    try:
                        objstore_id, varint_raw = (
                            ccl_chromium_indexeddb.custom_le_varint_from_bytes(
                                record.key[len(prefix_objectstore) :]
                            )
                        )
                    except TypeError:
                        continue

                    meta_type = record.key[len(prefix_objectstore) + len(varint_raw)]
                    old_version = objectstore_metadata_raw.get(
                        (db_id.dbid_no, objstore_id, meta_type)
                    )

                    if old_version is None or old_version.seq < record.seq:
                        objectstore_metadata_raw[
                            (db_id.dbid_no, objstore_id, meta_type)
                        ] = record

        database_metadata = ccl_chromium_indexeddb.DatabaseMetadata(
            database_metadata_raw
        )
        object_store_meta = ccl_chromium_indexeddb.ObjectStoreMetadata(
            objectstore_metadata_raw
        )

        # Extract records from stores we care about
        stores_of_interest = ["replychains", "conversations", "people", "buddylist"]
        blink_deserializer = ccl_blink_value_deserializer.BlinkV8Deserializer()

        results = []
        for global_id in global_metadata.db_ids:
            max_objstore = database_metadata.get_meta(
                global_id.dbid_no,
                ccl_chromium_indexeddb.DatabaseMetadataType.MaximumObjectStoreId,
            )

            for object_store_id in range(1, max_objstore + 1):
                datastore = object_store_meta.get_meta(
                    global_id.dbid_no,
                    object_store_id,
                    ccl_chromium_indexeddb.ObjectStoreMetadataType.StoreName,
                )

                if datastore not in stores_of_interest:
                    continue

                prefix = bytes([0, global_id.dbid_no, object_store_id, 1])
                for record in fetched_records:
                    if record.key.startswith(prefix) and record.value != b"":
                        try:
                            value_version, varint_raw = (
                                ccl_chromium_indexeddb.custom_le_varint_from_bytes(
                                    record.value
                                )
                            )
                            val_idx = len(varint_raw)

                            blink_type_tag = record.value[val_idx]
                            if blink_type_tag != 0xFF:
                                continue
                            val_idx += 1

                            blink_version, varint_raw = (
                                ccl_chromium_indexeddb.custom_le_varint_from_bytes(
                                    record.value[val_idx:]
                                )
                            )
                            val_idx += len(varint_raw)

                            obj_raw = io.BytesIO(record.value[val_idx:])
                            deserializer = ccl_v8_value_deserializer.Deserializer(
                                obj_raw, host_object_delegate=blink_deserializer.read
                            )
                            value = deserializer.read()

                            results.append(
                                {"store": datastore, "value": value, "seq": record.seq}
                            )
                        except Exception:
                            continue

        self._data = results
        self._build_indices()

    def _build_indices(self):
        """Build indices for fast lookup"""
        for item in self._data:
            if item["store"] == "replychains":
                mm = item["value"]["messageMap"]
                for msg_id, msg in mm.items():
                    conv_id = msg["conversationId"]
                    if conv_id not in self._messages:
                        self._messages[conv_id] = []
                    self._messages[conv_id].append(msg)

            elif item["store"] == "conversations":
                conv = item["value"]
                cid = conv["id"]
                self._conversations[cid] = conv

                # Build user map from members
                if "members" in conv:
                    for member in conv["members"]:
                        if "nameHint" in member and "displayName" in member["nameHint"]:
                            self._user_map[member["id"]] = member["nameHint"][
                                "displayName"
                            ]

                # Also get names from lastMessage
                if "lastMessage" in conv and isinstance(conv["lastMessage"], dict):
                    who = conv["lastMessage"].get("from", "")
                    if who.startswith("worker/"):
                        who = who[7:]
                    if conv["lastMessage"].get("imdisplayname"):
                        self._user_map[who] = conv["lastMessage"]["imdisplayname"]

    def _resolve_user(self, user_id: str) -> str:
        """Resolve user ID to display name"""
        return self._user_map.get(user_id, user_id)

    def _format_timestamp(self, ms: int) -> str:
        """Convert millisecond timestamp to ISO format"""
        return datetime.fromtimestamp(ms / 1000).isoformat()

    def _convert_html(self, content: str) -> str:
        """Convert HTML content to readable text"""
        if not content:
            return ""
        return self.h2t.handle(content).strip()

    def get_conversations(
        self, conv_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all conversations, optionally filtered by type"""
        self._parse_indexeddb()

        results = []
        for cid, conv in self._conversations.items():
            if conv_type and conv.get("type") != conv_type:
                continue

            result = {
                "id": cid,
                "type": conv.get("type"),
                "members": [],
                "message_count": len(self._messages.get(cid, [])),
            }

            # Add title/topic
            if conv.get("type") == "Meeting" and "threadProperties" in conv:
                result["title"] = conv["threadProperties"].get("topic")
            elif conv.get("type") == "Space" and "threadProperties" in conv:
                result["title"] = conv["threadProperties"].get("spaceThreadTopic")
            elif conv.get("type") == "Topic" and "threadProperties" in conv:
                result["title"] = conv["threadProperties"].get("topicThreadTopic")

            # Add members
            if "members" in conv:
                for member in conv["members"]:
                    result["members"].append(
                        {"id": member["id"], "name": self._resolve_user(member["id"])}
                    )

            # Add last message timestamp
            if "lastMessage" in conv and isinstance(conv["lastMessage"], dict):
                if "originalArrivalTime" in conv["lastMessage"]:
                    result["last_message_time"] = self._format_timestamp(
                        conv["lastMessage"]["originalArrivalTime"]
                    )

            results.append(result)

        return results

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        self._parse_indexeddb()

        if conversation_id not in self._messages:
            return []

        messages = []
        for msg in sorted(
            self._messages[conversation_id],
            key=lambda m: m.get("originalArrivalTime", 0),
        ):
            content = msg.get("content")
            msg_type = msg.get("messageType", "")

            # Convert HTML to text
            if msg_type == "RichText/Html" and content:
                content = self._convert_html(content)

            messages.append(
                {
                    "timestamp": self._format_timestamp(
                        msg.get("originalArrivalTime", 0)
                    ),
                    "sender": msg.get("imDisplayName", "Unknown"),
                    "sender_id": msg.get("from", ""),
                    "content": content,
                    "type": msg_type,
                }
            )

        return messages

    def search_messages(
        self, query: str, from_user: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search messages across all conversations"""
        self._parse_indexeddb()

        results = []
        query_lower = query.lower()

        for conv_id, messages in self._messages.items():
            for msg in messages:
                # Filter by user if specified
                if (
                    from_user
                    and from_user.lower() not in msg.get("imDisplayName", "").lower()
                ):
                    continue

                # Search in content
                content = msg.get("content", "")
                if content and query_lower in content.lower():
                    results.append(
                        {
                            "conversation_id": conv_id,
                            "timestamp": self._format_timestamp(
                                msg.get("originalArrivalTime", 0)
                            ),
                            "sender": msg.get("imDisplayName", "Unknown"),
                            "content": self._convert_html(content)
                            if msg.get("messageType") == "RichText/Html"
                            else content,
                            "match_snippet": content[:200],
                        }
                    )

                    if len(results) >= limit:
                        return results

        return results

    def get_summary(self) -> Dict[str, Any]:
        """Get cache summary statistics"""
        self._parse_indexeddb()

        total_messages = sum(len(msgs) for msgs in self._messages.values())

        return {
            "total_conversations": len(self._conversations),
            "total_messages": total_messages,
            "total_users": len(self._user_map),
            "cache_path": self.cache_path,
        }
