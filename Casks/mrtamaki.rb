cask "mrtamaki" do
  version "1.5.0"
  sha256 "31a3617b0420b43bf4c4ac4972d0aa0a3bd7d5e8e69344782d8e4f611fbcb5a2"

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

    # venv-found: rich, requests, InquirerPy (for 1lookup)
    found_venv = target_path/"venv-found"
    system python3.to_s, "-m", "venv", found_venv.to_s
    system "#{found_venv}/bin/pip", "install", "--quiet", "rich", "requests", "InquirerPy"
  end

  uninstall delete: "#{HOMEBREW_PREFIX}/share/mrtamaki"

  caveats <<~EOS
    Add to ~/.zshrc (one-time setup, never changes between versions):
      source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"

    Required dependency:
      brew install romkatv/powerlevel10k/powerlevel10k

    Update:
      brew update && brew reinstall --cask mrtamaki && exec zsh

    Type 'mrtamaki' for help and available commands.
  EOS
end
