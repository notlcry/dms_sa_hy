# Copyright (c) 2011 VMware, Inc.  All Rights Reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

require 'rvc/namespace'
require 'rvc/connection'
require 'shellwords'

module RVC

class Shell
  attr_reader :fs, :completion
  attr_reader :connections, :connection
  attr_accessor :debug, :cmds

  def initialize
    @persist_ruby = false
    @fs = RVC::FS.new RVC::RootNode.new(self)
    @completion = RVC::Completion.new self
    @connection = NullConnection.new
    @connections = { }
    @debug = false
    @cmds = nil
  end

  def switch_connection name
    @connection = @connections[name] || fail("no such connection")
  end

  def inspect
    "#<RVC::Shell:#{object_id}>"
  end

  def eval_input input  
    begin
      eval_command input
    rescue SystemExit, IOError
      raise
    rescue RVC::Util::UserError, RuntimeError,  Trollop::CommandlineError
      if debug
        puts "#{$!.class}: #{$!.message}"
        puts $!.backtrace * "\n"
      else
        case $!
        when  RVC::Util::UserError
          puts $!.message
        else
          puts "#{$!.class}: #{$!.message}"
        end
      end
    rescue Exception
      puts "#{$!.class}: #{$!.message}"
      puts $!.backtrace * "\n"
    ensure
      $stdout.flush
    end
  end

  def self.parse_input input
    begin
      cmdpath, *args = Shellwords.shellwords(input)
    rescue ArgumentError # unmatched double quote
      cmdpath, *args = Shellwords.shellwords(input + '"')
    end
    return nil unless cmdpath
    cmdpath = cmdpath.split('.').map(&:to_sym)
    [cmdpath, args]
  end

  def eval_command input
    cmdpath, args = Shell.parse_input input

    RVC::Util.err "invalid input" unless cmdpath

    cmd = cmds.lookup cmdpath
    RVC::Util.err "invalid command" unless cmd

    begin
      args, opts = cmd.parser.parse args
    rescue Trollop::HelpNeeded
      cmd.parser.educate
      return
    end

    if cmd.parser.has_options?
      cmd.invoke *(args + [opts])
    else
      cmd.invoke *args
    end
  end


  def prompt
      "#{@fs.display_path}#{false ? '~' : '>'} "
  end

  BULTIN_MODULE_PATH = [File.expand_path(File.join(File.dirname(__FILE__), 'modules')),
                        File.join(ENV['HOME'], ".rvc")]
  ENV_MODULE_PATH = (ENV['RVC_MODULE_PATH'] || '').split ':'

  def reload_modules verbose=true
    @cmds = RVC::Namespace.new 'root', self, nil
    module_path = (BULTIN_MODULE_PATH+ENV_MODULE_PATH).select { |d| File.directory?(d) }
    module_path.each do |dir|
      @cmds.load_module_dir dir, verbose
    end
  end
end

end
