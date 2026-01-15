cask "mr-tamaki" do
  version "X.Y.Z"
  sha256 "<PUT_SHA256_HERE>"

  url "https://github.com/<OWNER>/<REPO>/releases/download/v#{version}/<ASSET>.zip"
  name "Mr. Tamaki"
  desc "Zsh toolkit installed into share for sourcing"
  homepage "https://github.com/<OWNER>/<REPO>"

  depends_on formula: "jq"
  depends_on formula: "python"
  depends_on formula: "zsh"

  stage_only true

  postflight do
    require "fileutils"

    target_path = File.expand_path("#{HOMEBREW_PREFIX}/share/mr-tamaki")
    staged_root = staged_path

    visible_entries = Dir.children(staged_root, encoding: "UTF-8").reject do |entry|
      entry.start_with?(".") || entry == "__MACOSX"
    end

    source_root =
      if visible_entries.length == 1 && File.directory?(File.join(staged_root, visible_entries.first))
        File.join(staged_root, visible_entries.first)
      else
        staged_root
      end

    FileUtils.rm_rf target_path
    FileUtils.mkdir_p target_path

    Dir.children(source_root, encoding: "UTF-8").each do |entry|
      next if entry.start_with?(".") || entry == "__MACOSX"

      FileUtils.cp_r File.join(source_root, entry), File.join(target_path, entry), preserve: true
    end
  end

  uninstall delete: "#{HOMEBREW_PREFIX}/share/mr-tamaki"

  caveats do
    target_path = "#{HOMEBREW_PREFIX}/share/mr-tamaki"
    entrypoints = Dir.glob(File.join(target_path, "*.{sh,zsh}")).select { |p| File.file?(p) }.sort
    suggested = entrypoints.length == 1 ? File.basename(entrypoints.first) : nil

    text = +"Installed into #{target_path}\n"
    if suggested
      text << "\nAdd to ~/.zshrc:\n  source \"$(brew --prefix)/share/mr-tamaki/#{suggested}\"\n"
    else
      text << "\nPick the entrypoint (list files):\n  ls -1 \"$(brew --prefix)/share/mr-tamaki\"\n"
      text << "Then add to ~/.zshrc:\n  source \"$(brew --prefix)/share/mr-tamaki/<ENTRYPOINT>.sh\"\n"
    end
    text << "\nDependencies:\n"
    text << "  brew install jq python powerlevel10k\n"
    text << "  # zsh and curl are built-in on macOS; install via brew if you prefer\n"
    text << "  python3 -m pip install --user rich\n"
    text
  end
end

