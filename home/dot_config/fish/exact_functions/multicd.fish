function multicd --description 'Expansion for .. abbreviations: each extra dot goes up one level'
    echo cd (string repeat -n (math (string length -- $argv[1]) - 1) ../)
end
