# Fish environment and aliases

# XDG variables
test -z "$XDG_CONFIG_HOME"; and set -gx XDG_CONFIG_HOME "$HOME/.config"
test -z "$XDG_DATA_HOME"; and set -gx XDG_DATA_HOME "$HOME/.local/share"
test -z "$XDG_STATE_HOME"; and set -gx XDG_STATE_HOME "$HOME/.local/state"
test -z "$XDG_CACHE_HOME"; and set -gx XDG_CACHE_HOME "$HOME/.cache"

fish_add_path $HOME/.local/bin

# Starship Prompt
if type -q starship
    starship init fish | source
    set -gx STARSHIP_CONFIG $XDG_CONFIG_HOME/starship/starship.toml
end

# duf helper
if type -q duf
    function df -d "Run duf with last argument if valid, else run duf"
        if set -q argv[-1] && test -e $argv[-1]
            duf $argv[-1]
        else
            duf
        end
    end
end

# Aliases
alias c='clear'
alias l='eza -lh --icons=auto'
alias ls='eza --icons=auto'
alias ll='eza -lha --icons=auto --sort=name --group-directories-first'
alias ld='eza -lhD --icons=auto'
alias lt='eza --icons=auto --tree'
alias g='git'
alias fastfetch='fastfetch --logo-type kitty'

# Directory navigation
alias ..='cd ..'
alias ...='cd ../..'
alias .3='cd ../../..'
alias .4='cd ../../../..'
alias .5='cd ../../../../..'

alias vc='code'
abbr mkdir 'mkdir -p'

set -g fish_greeting
