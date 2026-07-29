#!/bin/bash
# Setup keyboard shortcuts for OpenAnchor

add_shortcuts() {
  if [ -f ~/.zshrc ]; then RC_FILE=~/.zshrc
  elif [ -f ~/.bashrc ]; then RC_FILE=~/.bashrc
  else echo "❌ No shell config found"; return 1; fi
  
  if grep -q "dash-openanchor" "$RC_FILE"; then
    echo "⚠️  Already installed"; return 0
  fi
  
  cat >> "$RC_FILE" << 'ALIASES'

# OpenAnchor shortcuts
alias dash-openanchor='openanchor dashboard --static'
alias dash-openanchor-live='openanchor dashboard'
alias dash-openanchor-export='openanchor dashboard --export /tmp/${pkg}_metrics.json && echo ✓ Exported'
ALIASES
  
  echo "✅ Shortcuts added"; echo "   Run: source $RC_FILE"
}

remove_shortcuts() {
  sed -i '' '/# OpenAnchor shortcuts/,/alias dash-openanchor-export=/d' ~/.zshrc 2>/dev/null
  sed -i '' '/# OpenAnchor shortcuts/,/alias dash-openanchor-export=/d' ~/.bashrc 2>/dev/null
  echo "✅ Removed"
}

case "${1:-}" in --remove) remove_shortcuts ;; *) add_shortcuts ;; esac
