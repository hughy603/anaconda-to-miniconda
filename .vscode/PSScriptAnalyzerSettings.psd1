@{
    IncludeRules = @(
        'PSUseConsistentIndentation',
        'PSUseConsistentWhitespace',
        'PSUseConsistentNewlines',
        'PSUseConsistentSpacing',
        'PSUseConsistentLineEndings'
    )
    Rules = @{
        PSUseConsistentIndentation = @{
            Enable = $true
            IndentationSize = 4
            Kind = 'space'
        }
        PSUseConsistentWhitespace = @{
            Enable = $true
            CheckOpenBrace = $true
            CheckOpenParen = $true
            CheckOperator = $true
            CheckSeparator = $true
        }
        PSUseConsistentNewlines = @{
            Enable = $true
            NewlineAfterOpenBrace = $true
            NewlineAfterOpenParen = $true
            NewlineAfterCloseBrace = $true
            NewlineAfterCloseParen = $true
        }
        PSUseConsistentSpacing = @{
            Enable = $true
            CheckOpenBrace = $true
            CheckOpenParen = $true
            CheckOperator = $true
            CheckSeparator = $true
        }
        PSUseConsistentLineEndings = @{
            Enable = $true
            LineEnding = 'CRLF'
        }
    }
}
