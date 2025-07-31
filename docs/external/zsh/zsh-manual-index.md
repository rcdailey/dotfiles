# The Z Shell Manual

### Version 5.9

### Updated May 14, 2022

**Original documentation by Paul Falstad**

This is a texinfo version of the documentation for the Z Shell, originally by
Paul Falstad.

Permission is granted to make and distribute verbatim copies of
this manual provided the copyright notice and this permission notice
are preserved on all copies.

Permission is granted to copy and distribute modified versions of this
manual under the conditions for verbatim copying, provided also that the
entire resulting derived work is distributed under the terms of a
permission notice identical to this one.

Permission is granted to copy and distribute translations of this manual
into another language, under the above conditions for modified versions.

---

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| [ < ] | [ [>](The-Z-Shell-Manual.html#The-Z-Shell-Manual "Next section in reading order") ] |  | [[Contents](zsh_toc.html#SEC_Contents "Table of contents")] | [[Index](Concept-Index.html#Concept-Index "Index")] | [ [?](zsh_abt.html#SEC_About "About (help)") ] |

# The Z Shell Manual

This Info file documents Zsh, a freely available UNIX command interpreter
(shell), which of the standard shells most closely resembles the Korn shell
(ksh), although it is not completely compatible. Zsh is able to emulate
POSIX shells, but its default mode is not POSIX compatible, either.

Version 5.9, last updated May 14, 2022.

|  |  |  |
| --- | --- | --- |
| [1 The Z Shell Manual](The-Z-Shell-Manual.html#The-Z-Shell-Manual) |  |  |
| [2 Introduction](Introduction.html#Introduction) |  |  |
| [3 Roadmap](Roadmap.html#Roadmap) |  |  |
| [4 Invocation](Invocation.html#Invocation) |  |  |
| [5 Files](Files.html#Files) |  |  |
| [6 Shell Grammar](Shell-Grammar.html#Shell-Grammar) |  |  |
| [7 Redirection](Redirection.html#Redirection) |  |  |
| [8 Command Execution](Command-Execution.html#Command-Execution) |  |  |
| [9 Functions](Functions.html#Functions) |  |  |
| [10 Jobs & Signals](Jobs-_0026-Signals.html#Jobs-_0026-Signals) |  |  |
| [11 Arithmetic Evaluation](Arithmetic-Evaluation.html#Arithmetic-Evaluation) |  |  |
| [12 Conditional Expressions](Conditional-Expressions.html#Conditional-Expressions) |  |  |
| [13 Prompt Expansion](Prompt-Expansion.html#Prompt-Expansion) |  |  |
| [14 Expansion](Expansion.html#Expansion) |  |  |
| [15 Parameters](Parameters.html#Parameters) |  |  |
| [16 Options](Options.html#Options) |  |  |
| [17 Shell Builtin Commands](Shell-Builtin-Commands.html#Shell-Builtin-Commands) |  |  |
| [18 Zsh Line Editor](Zsh-Line-Editor.html#Zsh-Line-Editor) |  |  |
| [19 Completion Widgets](Completion-Widgets.html#Completion-Widgets) |  |  |
| [20 Completion System](Completion-System.html#Completion-System) |  |  |
| [21 Completion Using compctl](Completion-Using-compctl.html#Completion-Using-compctl) |  |  |
| [22 Zsh Modules](Zsh-Modules.html#Zsh-Modules) |  |  |
| [23 Calendar Function System](Calendar-Function-System.html#Calendar-Function-System) |  |  |
| [24 TCP Function System](TCP-Function-System.html#TCP-Function-System) |  |  |
| [25 Zftp Function System](Zftp-Function-System.html#Zftp-Function-System) |  |  |
| [26 User Contributions](User-Contributions.html#User-Contributions) |  |  |
| ```  — Indices —   ``` | | |
| [Concept Index](Concept-Index.html#Concept-Index) |  |  |
| [Variables Index](Variables-Index.html#Variables-Index) |  |  |
| [Options Index](Options-Index.html#Options-Index) |  |  |
| [Functions Index](Functions-Index.html#Functions-Index) |  |  |
| [Editor Functions Index](Editor-Functions-Index.html#Editor-Functions-Index) |  |  |
| [Style and Tag Index](Style-and-Tag-Index.html#Style-and-Tag-Index) |  |  |
| ```  — The Detailed Node Listing —  Introduction   ``` | | |
| [2.1 Author](Introduction.html#Author) |  |  |
| [2.2 Availability](Introduction.html#Availability) |  |  |
| [2.3 Mailing Lists](Introduction.html#Mailing-Lists) |  |  |
| [2.4 The Zsh FAQ](Introduction.html#The-Zsh-FAQ) |  |  |
| [2.5 The Zsh Web Page](Introduction.html#The-Zsh-Web-Page) |  |  |
| [2.6 The Zsh Userguide](Introduction.html#The-Zsh-Userguide) |  |  |
| [2.7 See Also](Introduction.html#See-Also) |  |  |
| ```  Invocation   ``` | | |
| [4.2 Compatibility](Invocation.html#Compatibility) |  |  |
| [4.3 Restricted Shell](Invocation.html#Restricted-Shell) |  |  |
| ```  Shell Grammar   ``` | | |
| [6.1 Simple Commands & Pipelines](Shell-Grammar.html#Simple-Commands-_0026-Pipelines) |  |  |
| [6.2 Precommand Modifiers](Shell-Grammar.html#Precommand-Modifiers) |  |  |
| [6.3 Complex Commands](Shell-Grammar.html#Complex-Commands) |  |  |
| [6.4 Alternate Forms For Complex Commands](Shell-Grammar.html#Alternate-Forms-For-Complex-Commands) |  |  |
| [6.5 Reserved Words](Shell-Grammar.html#Reserved-Words) |  |  |
| [6.7 Comments](Shell-Grammar.html#Comments) |  |  |
| [6.8 Aliasing](Shell-Grammar.html#Aliasing) |  |  |
| [6.9 Quoting](Shell-Grammar.html#Quoting) |  |  |
| ```  Expansion   ``` | | |
| [14.1 History Expansion](Expansion.html#History-Expansion) |  |  |
| [14.2 Process Substitution](Expansion.html#Process-Substitution) |  |  |
| [14.3 Parameter Expansion](Expansion.html#Parameter-Expansion) |  |  |
| [14.4 Command Substitution](Expansion.html#Command-Substitution) |  |  |
| [14.5 Arithmetic Expansion](Expansion.html#Arithmetic-Expansion) |  |  |
| [14.6 Brace Expansion](Expansion.html#Brace-Expansion) |  |  |
| [14.7 Filename Expansion](Expansion.html#Filename-Expansion) |  |  |
| [14.8 Filename Generation](Expansion.html#Filename-Generation) |  |  |
| ```  Parameters   ``` | | |
| [15.2 Array Parameters](Parameters.html#Array-Parameters) |  |  |
| [15.3 Positional Parameters](Parameters.html#Positional-Parameters) |  |  |
| [15.4 Local Parameters](Parameters.html#Local-Parameters) |  |  |
| [15.5 Parameters Set By The Shell](Parameters.html#Parameters-Set-By-The-Shell) |  |  |
| [15.6 Parameters Used By The Shell](Parameters.html#Parameters-Used-By-The-Shell) |  |  |
| ```  Options   ``` | | |
| [16.1 Specifying Options](Options.html#Specifying-Options) |  |  |
| [16.2 Description of Options](Options.html#Description-of-Options) |  |  |
| [16.3 Option Aliases](Options.html#Option-Aliases) |  |  |
| [16.4 Single Letter Options](Options.html#Single-Letter-Options) |  |  |
| ```  Zsh Line Editor   ``` | | |
| [18.2 Keymaps](Zsh-Line-Editor.html#Keymaps) |  |  |
| [18.3 Zle Builtins](Zsh-Line-Editor.html#Zle-Builtins) |  |  |
| [18.4 Zle Widgets](Zsh-Line-Editor.html#Zle-Widgets) |  |  |
| [18.5 User-Defined Widgets](Zsh-Line-Editor.html#User_002dDefined-Widgets) |  |  |
| [18.6 Standard Widgets](Zsh-Line-Editor.html#Standard-Widgets) |  |  |
| [18.7 Character Highlighting](Zsh-Line-Editor.html#Character-Highlighting) |  |  |
| ```  Completion Widgets   ``` | | |
| [19.2 Completion Special Parameters](Completion-Widgets.html#Completion-Special-Parameters) |  |  |
| [19.3 Completion Builtin Commands](Completion-Widgets.html#Completion-Builtin-Commands) |  |  |
| [19.4 Completion Condition Codes](Completion-Widgets.html#Completion-Condition-Codes) |  |  |
| [19.5 Completion Matching Control](Completion-Widgets.html#Completion-Matching-Control) |  |  |
| [19.6 Completion Widget Example](Completion-Widgets.html#Completion-Widget-Example) |  |  |
| ```  Completion System   ``` | | |
| [20.2 Initialization](Completion-System.html#Initialization) |  |  |
| [20.3 Completion System Configuration](Completion-System.html#Completion-System-Configuration) |  |  |
| [20.4 Control Functions](Completion-System.html#Control-Functions) |  |  |
| [20.5 Bindable Commands](Completion-System.html#Bindable-Commands) |  |  |
| [20.6 Utility Functions](Completion-System.html#Completion-Functions) |  |  |
| [20.8 Completion Directories](Completion-System.html#Completion-Directories) |  |  |
| ```  Completion Using compctl   ``` | | |
| [21.3 Command Flags](Completion-Using-compctl.html#Command-Flags) |  |  |
| [21.4 Option Flags](Completion-Using-compctl.html#Option-Flags) |  |  |
| [21.5 Alternative Completion](Completion-Using-compctl.html#Alternative-Completion) |  |  |
| [21.6 Extended Completion](Completion-Using-compctl.html#Extended-Completion) |  |  |
| [21.7 Example](Completion-Using-compctl.html#Example) |  |  |
| ```  Zsh Modules   ``` | | |
| [22.2 The zsh/attr Module](Zsh-Modules.html#The-zsh_002fattr-Module) |  |  |
| [22.3 The zsh/cap Module](Zsh-Modules.html#The-zsh_002fcap-Module) |  |  |
| [22.4 The zsh/clone Module](Zsh-Modules.html#The-zsh_002fclone-Module) |  |  |
| [22.5 The zsh/compctl Module](Zsh-Modules.html#The-zsh_002fcompctl-Module) |  |  |
| [22.6 The zsh/complete Module](Zsh-Modules.html#The-zsh_002fcomplete-Module) |  |  |
| [22.7 The zsh/complist Module](Zsh-Modules.html#The-zsh_002fcomplist-Module) |  |  |
| [22.8 The zsh/computil Module](Zsh-Modules.html#The-zsh_002fcomputil-Module) |  |  |
| [22.9 The zsh/curses Module](Zsh-Modules.html#The-zsh_002fcurses-Module) |  |  |
| [22.10 The zsh/datetime Module](Zsh-Modules.html#The-zsh_002fdatetime-Module) |  |  |
| [22.11 The zsh/db/gdbm Module](Zsh-Modules.html#The-zsh_002fdb_002fgdbm-Module) |  |  |
| [22.12 The zsh/deltochar Module](Zsh-Modules.html#The-zsh_002fdeltochar-Module) |  |  |
| [22.13 The zsh/example Module](Zsh-Modules.html#The-zsh_002fexample-Module) |  |  |
| [22.14 The zsh/files Module](Zsh-Modules.html#The-zsh_002ffiles-Module) |  |  |
| [22.15 The zsh/langinfo Module](Zsh-Modules.html#The-zsh_002flanginfo-Module) |  |  |
| [22.16 The zsh/mapfile Module](Zsh-Modules.html#The-zsh_002fmapfile-Module) |  |  |
| [22.17 The zsh/mathfunc Module](Zsh-Modules.html#The-zsh_002fmathfunc-Module) |  |  |
| [22.18 The zsh/nearcolor Module](Zsh-Modules.html#The-zsh_002fnearcolor-Module) |  |  |
| [22.19 The zsh/newuser Module](Zsh-Modules.html#The-zsh_002fnewuser-Module) |  |  |
| [22.20 The zsh/parameter Module](Zsh-Modules.html#The-zsh_002fparameter-Module) |  |  |
| [22.21 The zsh/pcre Module](Zsh-Modules.html#The-zsh_002fpcre-Module) |  |  |
| [22.22 The zsh/param/private Module](Zsh-Modules.html#The-zsh_002fparam_002fprivate-Module) |  |  |
| [22.23 The zsh/regex Module](Zsh-Modules.html#The-zsh_002fregex-Module) |  |  |
| [22.24 The zsh/sched Module](Zsh-Modules.html#The-zsh_002fsched-Module) |  |  |
| [22.25 The zsh/net/socket Module](Zsh-Modules.html#The-zsh_002fnet_002fsocket-Module) |  |  |
| [22.26 The zsh/stat Module](Zsh-Modules.html#The-zsh_002fstat-Module) |  |  |
| [22.27 The zsh/system Module](Zsh-Modules.html#The-zsh_002fsystem-Module) |  |  |
| [22.28 The zsh/net/tcp Module](Zsh-Modules.html#The-zsh_002fnet_002ftcp-Module) |  |  |
| [22.29 The zsh/termcap Module](Zsh-Modules.html#The-zsh_002ftermcap-Module) |  |  |
| [22.30 The zsh/terminfo Module](Zsh-Modules.html#The-zsh_002fterminfo-Module) |  |  |
| [22.31 The zsh/watch Module](Zsh-Modules.html#The-zsh_002fwatch-Module) |  |  |
| [22.32 The zsh/zftp Module](Zsh-Modules.html#The-zsh_002fzftp-Module) |  |  |
| [22.33 The zsh/zle Module](Zsh-Modules.html#The-zsh_002fzle-Module) |  |  |
| [22.34 The zsh/zleparameter Module](Zsh-Modules.html#The-zsh_002fzleparameter-Module) |  |  |
| [22.35 The zsh/zprof Module](Zsh-Modules.html#The-zsh_002fzprof-Module) |  |  |
| [22.36 The zsh/zpty Module](Zsh-Modules.html#The-zsh_002fzpty-Module) |  |  |
| [22.37 The zsh/zselect Module](Zsh-Modules.html#The-zsh_002fzselect-Module) |  |  |
| [22.38 The zsh/zutil Module](Zsh-Modules.html#The-zsh_002fzutil-Module) |  |  |
| ```  Calendar Function System   ``` | | |
| [23.2 File and Date Formats](Calendar-Function-System.html#Calendar-File-and-Date-Formats) |  |  |
| [23.3 User Functions](Calendar-Function-System.html#Calendar-System-User-Functions) |  |  |
| [23.4 Styles](Calendar-Function-System.html#Calendar-Styles) |  |  |
| [23.5 Utility functions](Calendar-Function-System.html#Calendar-Utility-Functions) |  |  |
| [23.6 Bugs](Calendar-Function-System.html#Calendar-Bugs) |  |  |
| ```  TCP Function System   ``` | | |
| [24.2 TCP User Functions](TCP-Function-System.html#TCP-Functions) |  |  |
| [24.5 TCP User Parameters](TCP-Function-System.html#TCP-Parameters) |  |  |
| [24.8 TCP Examples](TCP-Function-System.html#TCP-Examples) |  |  |
| [24.9 TCP Bugs](TCP-Function-System.html#TCP-Bugs) |  |  |
| ```  Zftp Function System   ``` | | |
| [25.2 Installation](Zftp-Function-System.html#Installation) |  |  |
| [25.3 Functions](Zftp-Function-System.html#Zftp-Functions) |  |  |
| [25.4 Miscellaneous Features](Zftp-Function-System.html#Miscellaneous-Features) |  |  |
| ```  User Contributions   ``` | | |
| [26.2 Utilities](User-Contributions.html#Utilities) |  |  |
| [26.3 Remembering Recent Directories](User-Contributions.html#Recent-Directories) |  |  |
| [26.4 Abbreviated dynamic references to directories](User-Contributions.html#Other-Directory-Functions) |  |  |
| [26.5 Gathering information from version control systems](User-Contributions.html#Version-Control-Information) |  |  |
| [26.6 Prompt Themes](User-Contributions.html#Prompt-Themes) |  |  |
| [26.7 ZLE Functions](User-Contributions.html#ZLE-Functions) |  |  |
| [26.8 Exception Handling](User-Contributions.html#Exception-Handling) |  |  |
| [26.9 MIME Functions](User-Contributions.html#MIME-Functions) |  |  |
| [26.10 Mathematical Functions](User-Contributions.html#Mathematical-Functions) |  |  |
| [26.11 User Configuration Functions](User-Contributions.html#User-Configuration-Functions) |  |  |
| [26.12 Other Functions](User-Contributions.html#Other-Functions) |  |  |
| ```   ``` | | |

---

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| [ < ] | [ [>](The-Z-Shell-Manual.html#The-Z-Shell-Manual "Next section in reading order") ] |  | [[Contents](zsh_toc.html#SEC_Contents "Table of contents")] | [[Index](Concept-Index.html#Concept-Index "Index")] | [ [?](zsh_abt.html#SEC_About "About (help)") ] |

This document was generated on *May 14, 2022* using [*texi2html 5.0*](http://www.nongnu.org/texi2html/).

Zsh version 5.9, released on May 14, 2022.
