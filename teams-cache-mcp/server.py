"""
MS Teams Cache MCP Server

FastMCP server providing read-only access to local MS Teams cache data.
"""

from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
from teams_parser import TeamsCache

mcp = FastMCP("Teams Cache")

# Global cache instance (lazy-loaded)
_cache: Optional[TeamsCache] = None


def get_cache() -> TeamsCache:
    """Get or initialize the Teams cache parser"""
    global _cache
    if _cache is None:
        _cache = TeamsCache()
    return _cache


@mcp.tool
def search_messages(
    query: str, from_user: Optional[str] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search across all Teams conversations by keyword.

    Args:
        query: Search term to find in message content
        from_user: Optional filter by sender name (partial match)
        limit: Maximum number of results to return (default: 50)

    Returns:
        List of matching messages with conversation context
    """
    cache = get_cache()
    return cache.search_messages(query, from_user, limit)


@mcp.tool
def get_conversation(
    conversation_id: str, include_system_messages: bool = False
) -> Dict[str, Any]:
    """
    Retrieve full conversation history by ID.

    Args:
        conversation_id: The Teams conversation ID
        include_system_messages: Include system/activity messages (default: False)

    Returns:
        Conversation metadata and chronological message list
    """
    cache = get_cache()

    # Get conversation metadata
    convs = [c for c in cache.get_conversations() if c["id"] == conversation_id]
    if not convs:
        return {"error": f"Conversation {conversation_id} not found"}

    conv = convs[0]
    messages = cache.get_messages(conversation_id)

    # Filter system messages if requested
    if not include_system_messages:
        messages = [m for m in messages if not m["type"].startswith("ThreadActivity/")]

    return {"conversation": conv, "messages": messages}


@mcp.tool
def list_conversations(
    conversation_type: Optional[str] = None, limit: int = 100
) -> List[Dict[str, Any]]:
    """
    List all available conversations with filters.

    Args:
        conversation_type: Filter by type (Chat, Meeting, Space, Topic, Thread, Conversation)
        limit: Maximum number of results (default: 100)

    Returns:
        Summary list with titles, participants, and last message timestamps
    """
    cache = get_cache()
    convs = cache.get_conversations(conversation_type)
    return convs[:limit]


@mcp.tool
def get_call_history(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve call logs with participants and timestamps.

    Args:
        limit: Maximum number of call records (default: 50)

    Returns:
        Call records with participants, timestamps, and duration
    """
    cache = get_cache()

    # Get Thread type conversations (call logs)
    convs = cache.get_conversations("Thread")
    if not convs:
        return []

    # Get messages from call log conversations
    results = []
    for conv in convs:
        messages = cache.get_messages(conv["id"])
        for msg in messages:
            if msg["type"] == "Event/Call" or "call" in msg.get("content", "").lower():
                results.append(
                    {
                        "timestamp": msg["timestamp"],
                        "participants": conv.get("members", []),
                        "details": msg["content"],
                    }
                )

                if len(results) >= limit:
                    return results

    return results


@mcp.tool
def get_participants(conversation_id: str) -> List[Dict[str, str]]:
    """
    Get participant info for a specific conversation.

    Args:
        conversation_id: The Teams conversation ID

    Returns:
        List of participants with display names and IDs
    """
    cache = get_cache()
    convs = [c for c in cache.get_conversations() if c["id"] == conversation_id]

    if not convs:
        return []

    return convs[0].get("members", [])


@mcp.tool
def get_user_stats(user_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate statistics about conversations and activity.

    Args:
        user_name: Optional user to get stats for (default: all users)

    Returns:
        Message counts, active conversations, and activity metrics
    """
    cache = get_cache()
    summary = cache.get_summary()

    if user_name:
        # Count messages from specific user
        user_message_count = 0
        for conv_id in cache._messages:
            for msg in cache._messages[conv_id]:
                if user_name.lower() in msg.get("imDisplayName", "").lower():
                    user_message_count += 1

        summary["user_message_count"] = user_message_count
        summary["user_name"] = user_name

    return summary


@mcp.tool
def search_by_participant(
    participant_name: str, conversation_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find all conversations involving specific participants.

    Args:
        participant_name: Name to search for (partial match)
        conversation_type: Optional filter by conversation type

    Returns:
        List of conversations with those participants
    """
    cache = get_cache()
    convs = cache.get_conversations(conversation_type)

    results = []
    participant_lower = participant_name.lower()

    for conv in convs:
        for member in conv.get("members", []):
            if participant_lower in member["name"].lower():
                results.append(conv)
                break

    return results


@mcp.resource("teams://cache/summary")
def cache_summary() -> str:
    """Overview of Teams cache contents"""
    cache = get_cache()
    summary = cache.get_summary()

    return f"""# Teams Cache Summary

**Total Conversations:** {summary["total_conversations"]}
**Total Messages:** {summary["total_messages"]}
**Total Users:** {summary["total_users"]}

**Cache Location:** {summary["cache_path"]}
"""


@mcp.resource("teams://conversations/list")
def conversations_list() -> str:
    """Complete list of all conversations with metadata"""
    cache = get_cache()
    convs = cache.get_conversations()

    lines = ["# Teams Conversations\n"]
    for conv in convs:
        title = conv.get("title", f"Conversation {conv['id'][:8]}")
        conv_type = conv.get("type", "Unknown")
        msg_count = conv.get("message_count", 0)
        member_count = len(conv.get("members", []))

        lines.append(f"## {title}")
        lines.append(f"- **Type:** {conv_type}")
        lines.append(f"- **ID:** {conv['id']}")
        lines.append(f"- **Messages:** {msg_count}")
        lines.append(f"- **Participants:** {member_count}")

        if "last_message_time" in conv:
            lines.append(f"- **Last Activity:** {conv['last_message_time']}")

        lines.append("")

    return "\n".join(lines)


@mcp.resource("teams://participants/directory")
def participants_directory() -> str:
    """Directory of all known participants with resolved names"""
    cache = get_cache()
    cache._parse_indexeddb()  # Ensure data is loaded

    lines = ["# Teams Participants Directory\n"]
    for user_id, name in sorted(cache._user_map.items(), key=lambda x: x[1]):
        lines.append(f"- **{name}** (`{user_id}`)")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
