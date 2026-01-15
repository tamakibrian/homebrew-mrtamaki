cask "mrtamaki" do
  version "1.1"
  sha256 :no_check

  url "https://github.com/tamakibrian/homebrew-mrtamaki/releases/download/v#{version}/mrtamaki-#{version}.zip",
      verified: "github.com/tamakibrian/homebrew-mrtamaki"
  name "mrtamaki"
  desc "Zsh toolkit installed into share for sourcing"
  homepage "https://github.com/tamakibrian/homebrew-mrtamaki"

  depends_on formula: "jq"
  depends_on formula: "python"
  depends_on formula: "zsh"
  depends_on formula: "romkatv/powerlevel10k/powerlevel10k"

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
  end

  uninstall delete: "#{HOMEBREW_PREFIX}/share/mrtamaki"

  caveats <<~EOS
    Installed into $(brew --prefix)/share/mrtamaki

    Add to ~/.zshrc:
      source "$(brew --prefix)/share/mrtamaki/v1.1.sh"

    For the animated banner, install the Rich Python library:
      python3 -m pip install --user rich
  EOS
end
