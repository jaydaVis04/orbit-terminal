# Shared terminal theme integration. Safe to source more than once.
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
  export PATH="$HOME/bin:$PATH"
fi

# Display the launch card once per Kitty shell session, outside tmux and SSH.
if [[ ${ORBIT_WELCOME:-1} == 1 && -o interactive && -n ${KITTY_WINDOW_ID:-} && -z ${TMUX:-} \
      && -z ${SSH_CONNECTION:-} && -z ${SSH_CLIENT:-} && -z ${SSH_TTY:-} \
      && -z ${TERMINAL_RICE_WELCOME_SHOWN:-} ]]; then
  export TERMINAL_RICE_WELCOME_SHOWN=1
  if [[ -r "$HOME/.config/terminal-themes/active" \
        && "$(<"$HOME/.config/terminal-themes/active")" == space ]] \
        && (( $+commands[neofetch] )); then
    command neofetch --config "$HOME/.config/neofetch/config.conf"
  fi
fi
