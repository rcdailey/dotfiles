# Teams Cache MCP Server

Read-only MCP server providing access to local Microsoft Teams cache data. Enables LLMs to search conversations, retrieve messages, and analyze Teams activity from your local cache.

## Features

**7 Tools:**

- `search_messages` - Search across all conversations by keyword
- `get_conversation` - Retrieve full conversation history
- `list_conversations` - List all conversations with filters
- `get_call_history` - Retrieve call logs
- `get_participants` - Get participant info for conversations
- `get_user_stats` - Generate activity statistics
- `search_by_participant` - Find conversations by participant

**3 Resources:**

- `teams://cache/summary` - Cache overview and statistics
- `teams://conversations/list` - Complete conversation listing
- `teams://participants/directory` - User directory with names

## Installation

### Prerequisites

- Python 3.8+
- Microsoft Teams installed with local cache
- `uv` package manager (for FastMCP)

### Install to Claude Code

```bash
fastmcp install claude-code server.py --with html2text
```

### Install to Other Clients

```bash
# Claude Desktop
fastmcp install claude-desktop server.py --with html2text

# Cursor
fastmcp install cursor server.py --with html2text

# Generic MCP JSON config
fastmcp install mcp-json server.py --with html2text
```

## Usage Examples

### Search Messages

```
Find all messages from Sarah about "project deadline"
```

### Get Conversation

```
Show me the full history of the "Design Review" meeting
```

### List Conversations

```
List all my Chat conversations
```

### Call History

```
Show me my recent Teams calls
```

### Participant Search

```
Find all conversations with John and Mike
```

### Statistics

```
How many messages has Sarah sent?
```

## Cache Locations

The server automatically detects your Teams cache based on platform:

**macOS (Teams 2.X):**

```
~/Library/Containers/com.microsoft.teams2/Data/Library/Application Support/Microsoft/MSTeams/EBWebView/WV2Profile_tfw/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb
```

**macOS (Teams 1.X):**

```
~/Library/Application Support/Microsoft/Teams/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb
```

**Windows (Teams 2.X):**

```
%LOCALAPPDATA%\Packages\MicrosoftTeams_8wekyb3d8bbwe\LocalCache\Microsoft\MSTeams\EBWebView\Default\IndexedDB\https_teams.microsoft.com_0.indexeddb.leveldb
```

**Windows (Teams 1.X):**

```
%APPDATA%\Microsoft\Teams\IndexedDB\https_teams.microsoft.com_0.indexeddb.leveldb
```

**Linux:**

```
~/.config/Microsoft/Microsoft Teams/IndexedDB/https_teams.microsoft.com_0.indexeddb.leveldb
```

## Troubleshooting

### Cache Not Found

**Error:** `FileNotFoundError: Teams cache not found`

**Solution:** Ensure Microsoft Teams is installed and you've used it at least once to generate cache data.

### Teams is Running

**Warning:** Reading cache while Teams is running may return incomplete/stale data.

**Solution:** For best results, close Teams before querying the cache.

### Permission Denied

**Error:** `PermissionError` when reading cache

**Solution:** Ensure you have read permissions on the Teams cache directory.

### Empty Results

**Issue:** Search returns no results despite having conversations

**Solution:**

1. Verify cache path with `teams://cache/summary` resource
2. Check if Teams has synced recent messages
3. Close and reopen Teams to force cache update

## Development

### Run Development Server

```bash
fastmcp dev server.py --with html2text
```

### Test with MCP Inspector

```bash
fastmcp dev server.py
# Opens MCP Inspector in browser
```

## Privacy & Security

**Important Notes:**

- This server provides **read-only** access to your local cache
- No data is sent to external servers
- No modifications are made to Teams cache
- Cache data is parsed in-memory and not persisted
- Consider cache content sensitivity when sharing queries with LLMs

## Technical Details

**Architecture:**

- Built with [FastMCP](https://gofastmcp.com) framework
- Uses `ccl_chrome_indexeddb` for LevelDB parsing
- Pure Python implementation (no native dependencies)
- Lazy-loads cache data on first tool invocation
- Caches parsed data in memory for performance

**Data Sources:**

- IndexedDB stores: `replychains`, `conversations`, `people`, `buddylist`
- Message types: RichText/Html, ThreadActivity, Event/Call
- Conversation types: Chat, Meeting, Space, Topic, Thread, Conversation

## License

This project includes code from:

- [teams-decoder](https://github.com/Sec42/teams-decoder) (MIT License)
- [ccl_chrome_indexeddb](https://github.com/cclgroupltd/ccl_chrome_indexeddb) (MIT License)

See `ccl_chrome_indexeddb/LICENSE` for details.

## Contributing

This is a personal project. Feel free to fork and adapt for your needs.

## Disclaimer

This tool is not affiliated with Microsoft. Use at your own risk. Always respect data privacy and organizational policies when accessing and sharing Teams data.
