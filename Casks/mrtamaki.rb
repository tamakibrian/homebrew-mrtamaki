cask "mrtamaki" do
  version "1.8.0"
  sha256 "62a68a92139db4356c58534285393c632b0fd9576cd0819ac42c3c727edb9670"

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

    # Helper: create venv, upgrade pip silently, then install packages
    venvs = {
      "venv-banner" => %w[rich],
      "venv-files"  => %w[rich readchar],
      "venv-found"  => %w[rich requests InquirerPy readchar],
      "venv-status" => %w[rich readchar psutil],
      "venv-proxy"  => %w[PySocks rich readchar dnspython],
    }

    venvs.each do |name, packages|
      venv_path = target_path/name
      system python3.to_s, "-m", "venv", venv_path.to_s
      system "#{venv_path}/bin/pip", "install", "--quiet", "--upgrade", "pip"
      system "#{venv_path}/bin/pip", "install", "--quiet", *packages
    end

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
