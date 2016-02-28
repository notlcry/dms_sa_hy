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

require 'rvc/vim'

require 'terminal-table'



opts :help do
  summary "Display this text"
  arg :cmd, "Command or namespace to display help for", :required => false
end

rvc_alias :help

HELP_ORDER = %w(basic vm)

def help input
  if input
    cmdpath, args = Shell.parse_input input
    o = shell.cmds.lookup(cmdpath, Namespace) || shell.cmds.lookup(cmdpath)
    RVC::Util.err "invalid command or namespace" unless o
  else
    o = shell.cmds
  end

  case o
  when Command
    o.parser.educate
  when Namespace
    help_namespace o
  end

  # TODO apropos
  puts (<<-EOS)

To see commands in a namespace: help namespace_name
To see detailed help for a command: help namespace_name.command_name
  EOS
end

# TODO namespace summaries
def help_namespace ns
  unless ns.namespaces.empty?
    puts "Namespaces:"
    ns.namespaces.sort_by do |child_name,child|
      HELP_ORDER.index(child_name.to_s) || HELP_ORDER.size
    end.each do |child_name,child|
      puts child_name
    end
  end

  puts unless ns.namespaces.empty? or ns.commands.empty?

  unless ns.commands.empty?
    puts "Commands:"
    ns.commands.sort_by do |cmd_name,cmd|
      HELP_ORDER.index(cmd_name.to_s) || HELP_ORDER.size
    end.each do |cmd_name,cmd|
      help_summary cmd
    end
  end
end

def help_summary cmd
  aliases = shell.cmds.aliases.select { |k,v| shell.cmds.lookup(v) == cmd }.map(&:first)
  aliases_text = aliases.empty? ? '' : " (#{aliases*', '})"
  puts "#{cmd.name}#{aliases_text}: #{cmd.summary}"
end


opts :debug do
  summary "Toggle VMOMI logging to stderr"
end

rvc_alias :debug

def debug
  debug = shell.debug = !shell.debug
  shell.connections.each do |name,conn|
    conn.debug = debug if conn.respond_to? :debug
  end
  puts "debug mode #{debug ? 'en' : 'dis'}abled"
end


opts :cd do
  summary "Change directory"
  arg :obj, "Directory to change to", :lookup => Object
end

rvc_alias :cd

def cd obj
  shell.fs.cd(obj)
  #shell.fs.marks[''] = [find_ancestor(RbVmomi::VIM::Datacenter)].compact
  #shell.fs.marks['@'] = [find_ancestor(RbVmomi::VIM)].compact
  shell.fs.delete_numeric_marks
end

def find_ancestor klass
  shell.fs.cur.rvc_path.map { |k,v| v }.reverse.find { |x| x.is_a? klass }
end


opts :ls do
  summary "List objects in a directory"
  arg :obj, "Directory to list", :required => false, :default => '.', :lookup => Object
end

rvc_alias :ls
rvc_alias :ls, :l

def ls obj
  if obj.respond_to?(:rvc_ls)
    return obj.rvc_ls
  end
  puts obj.children
end

