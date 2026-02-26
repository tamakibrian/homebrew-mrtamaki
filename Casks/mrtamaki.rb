cask "mrtamaki" do
  version "1.12.5"
  sha256 "c5063630c11ed67272a44ffdf5c19c78201ccba5b1b6b820f30ff6fca01de93f"

  url "https://github.com/tamakibrian/homebrew-mrtamaki/releases/download/v#{version}/mrtamaki-#{version}.zip",
      verified: "github.com/tamakibrian/homebrew-mrtamaki"
  name "mrtamaki"
  desc "CLI toolkit for proxy, IP, system, lookup, and file operations"
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

    python3 = HOMEBREW_PREFIX/"bin/python3"

    # Create venv for mt CLI (Python package with all dependencies)
    venv_cli = target_path/"venv-cli"
    system python3.to_s, "-m", "venv", venv_cli.to_s
    system "#{venv_cli}/bin/pip", "install", "--quiet", "--upgrade", "pip"
    system "#{venv_cli}/bin/pip", "install", "--quiet", "-e", target_path.to_s

    # Symlink mt and mrtamaki into PATH
    bin_mt = venv_cli/"bin/mt"
    bin_mrtamaki = venv_cli/"bin/mrtamaki"
    FileUtils.ln_sf bin_mt.to_s, HOMEBREW_PREFIX/"bin/mt"
    FileUtils.ln_sf bin_mrtamaki.to_s, HOMEBREW_PREFIX/"bin/mrtamaki"

    # Create venv-banner for startup banner (banner.py)
    venv_banner = target_path/"venv-banner"
    system python3.to_s, "-m", "venv", venv_banner.to_s
    system "#{venv_banner}/bin/pip", "install", "--quiet", "--upgrade", "pip"
    system "#{venv_banner}/bin/pip", "install", "--quiet", "rich"

    # Install JetBrains Mono Nerd Font
    system HOMEBREW_PREFIX/"bin/brew", "install", "--cask", "font-jetbrains-mono-nerd-font"

    # Install light-zsh theme for Oh My Zsh (create dirs if needed)
    omz_custom_themes = Pathname.new(ENV["HOME"])/".oh-my-zsh"/"custom"/"themes"
    omz_custom_themes.mkpath
    light_zsh_dir = omz_custom_themes/"light-zsh"
    unless light_zsh_dir.exist?
      system "git", "clone", "--depth", "1",
             "https://github.com/InfinityUniverse0/light-zsh.git",
             light_zsh_dir.to_s
    end
  end

  uninstall delete: [
    "#{HOMEBREW_PREFIX}/share/mrtamaki",
    "#{HOMEBREW_PREFIX}/bin/mt",
    "#{HOMEBREW_PREFIX}/bin/mrtamaki",
  ]

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

    The 'mt' command is available in PATH. Type 'mt' or 'mrtamaki' for help.
  EOS
end
