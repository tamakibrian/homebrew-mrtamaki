cask "mrtamaki" do
  version "1.3.3"
  sha256 "fa74352a08f940ea10bbe6be3b75bfa4662e38c3e7d6cdc99e31288660dc655e"

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

    # Create venv and install rich for the banner
    venv_path = target_path/"venv"
    python3 = HOMEBREW_PREFIX/"bin/python3"
    system python3.to_s, "-m", "venv", venv_path.to_s
    system "#{venv_path}/bin/pip", "install", "--quiet", "rich"

    # Create venv for one_lookup and install dependencies
    onelookup_venv = target_path/"found/venv"
    system python3.to_s, "-m", "venv", onelookup_venv.to_s
    system "#{onelookup_venv}/bin/pip", "install", "--quiet", "rich", "requests", "InquirerPy"
  end

  uninstall delete: "#{HOMEBREW_PREFIX}/share/mrtamaki"

  caveats <<~EOS
    Add to ~/.zshrc:
      source "$(brew --prefix)/share/mrtamaki/v1.3.3.sh"

    Required dependency:
      brew install romkatv/powerlevel10k/powerlevel10k

    Update:
      brew update && brew reinstall --cask mrtamaki && exec zsh

    Type 'mrtamaki' for help and available commands.
  EOS
end
