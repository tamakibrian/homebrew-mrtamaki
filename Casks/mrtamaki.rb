cask "mrtamaki" do
  version "1.7.3"
  sha256 "15f7ee86a681e22121d80c5bc54e95e2995edf8fe0549183ee8a1574840511ee"

  url "https://github.com/tamakibrian/homebrew-mrtamaki/releases/download/v#{version}/mrtamaki-#{version}.zip",
      verified: "github.com/tamakibrian/homebrew-mrtamaki"
  name "mrtamaki"
  desc "Zsh toolkit installed into share for sourcing"
  homepage "https://github.com/tamakibrian/homebrew-mrtamaki"

  depends_on formula: "jq"
  depends_on formula: "python"
  depends_on formula: "zsh"
  depends_on formula: "zsh-syntax-highlighting"
  depends_on formula: "zsh-autosuggestions"

  stage_only true

  postflight do
    require "fileutils"

    target_path = HOMEBREW_PREFIX/"share/mrtamaki"
    staged_root = staged_path

    visible_entries = staged_root.children.reject do |entry|
      entry.basename.to_s.start_with?(".") || entry.basename.to_s == "__MACOSX"
    end

    source_root =
      if visible_entries.length == 1 && visible_entries.first.directory?
        visible_entries.first
      else
        staged_root
      end

    target_path.rmtree if target_path.exist?
    target_path.mkpath

    source_root.children.each do |entry|
      next if entry.basename.to_s.start_with?(".") || entry.basename.to_s == "__MACOSX"

      FileUtils.cp_r entry, target_path, preserve: true
    end

    # Create venvs with consistent naming in root directory
    python3 = HOMEBREW_PREFIX/"bin/python3"

    # venv-banner: rich (for startup banner)
    banner_venv = target_path/"venv-banner"
    system python3.to_s, "-m", "venv", banner_venv.to_s
    system "#{banner_venv}/bin/pip", "install", "--quiet", "rich"

    # venv-files: rich, readchar (for file menu)
    files_venv = target_path/"venv-files"
    system python3.to_s, "-m", "venv", files_venv.to_s
    system "#{files_venv}/bin/pip", "install", "--quiet", "rich", "readchar"

    # venv-found: rich, requests, InquirerPy, readchar (for 1lookup)
    found_venv = target_path/"venv-found"
    system python3.to_s, "-m", "venv", found_venv.to_s
    system "#{found_venv}/bin/pip", "install", "--quiet", "rich", "requests", "InquirerPy", "readchar"

    # venv-status: rich, readchar, psutil (for status menu and health dashboard)
    status_venv = target_path/"venv-status"
    system python3.to_s, "-m", "venv", status_venv.to_s
    system "#{status_venv}/bin/pip", "install", "--quiet", "rich", "readchar", "psutil"

    # venv-proxy: PySocks, rich, readchar, dnspython (for proxy converter)
    proxy_venv = target_path/"venv-proxy"
    system python3.to_s, "-m", "venv", proxy_venv.to_s
    system "#{proxy_venv}/bin/pip", "install", "--quiet", "PySocks", "rich", "readchar", "dnspython"

    # Install JetBrains Mono Nerd Font
    system HOMEBREW_PREFIX/"bin/brew", "install", "--cask", "font-jetbrains-mono-nerd-font"

    # Install light-zsh theme for Oh My Zsh
    omz_custom_themes = Pathname.new(ENV["HOME"])/".oh-my-zsh"/"custom"/"themes"
    if omz_custom_themes.exist?
      light_zsh_dir = omz_custom_themes/"light-zsh"
      unless light_zsh_dir.exist?
        system "git", "clone", "--depth", "1",
               "https://github.com/InfinityUniverse0/light-zsh.git",
               light_zsh_dir.to_s
      end
    end
  end

  uninstall delete: "#{HOMEBREW_PREFIX}/share/mrtamaki"

  caveats <<~EOS
    Add to ~/.zshrc (one-time setup, never changes between versions):
      source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"

    Included with install:
      - JetBrains Mono Nerd Font (font-jetbrains-mono-nerd-font)
      - light-zsh theme (cloned to ~/.oh-my-zsh/custom/themes/)
      - zsh-syntax-highlighting
      - zsh-autosuggestions

    Set your terminal font to "JetBrains Mono Nerd Font" for icon support.

    Update:
      brew update && brew reinstall --cask mrtamaki && exec zsh

    Type 'mrtamaki' for help and available commands.
  EOS
end
