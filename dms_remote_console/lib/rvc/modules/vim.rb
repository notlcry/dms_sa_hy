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

require 'rvc/known_hosts'
require 'rvc/vim'

RVC::SCHEMES['zookeeper'] = lambda { |uri| connect uri, {} }

opts :connect do
  summary 'Open a connection to ESX/VC'
  arg :uri, "Host to connect to"
  opt :rev, "Override protocol revision", :type => :string
end

rvc_alias :connect

def connect uri, opts
  uri = RVC::URIParser.parse uri unless uri.is_a? URI
  host = uri.host
  port = uri.port || 2181


  vim = nil
  loop do
    begin
      vim = DmsVmomi::VIM.new :host => host,
                             :port => port,
                             :type => 'zookeeper'
      break
    rescue 
      err $!.message
    end
  end

  vim.define_singleton_method(:_host) { host }

  conn_name = host.dup
  conn_name = "#{conn_name}:1" if shell.connections.member? conn_name
  conn_name.succ! while shell.connections.member? conn_name

  shell.connections[conn_name] = vim
end

def prompt_password
  ask("password: ") { |q| q.echo = false }
end

def keychain_password username , hostname
   return nil unless RbConfig::CONFIG['host_os'] =~ /^darwin1[01]/

  begin
    require 'osx_keychain'
  rescue LoadError
    return nil
  end

  keychain = OSXKeychain.new
  return keychain["rvc", "#{username}@#{hostname}" ]

end

def save_keychain_password username , password , hostname
  # only works for OSX at the minute.
  return false unless RbConfig::CONFIG['host_os'] =~ /^darwin10/

  # check we already managed to load that gem.
  if defined? OSXKeychain::VERSION

    if agree("Save password for connection (y/n)? ", true)
      keychain = OSXKeychain.new

      # update the keychain, unless it's already set to that.
      keychain.set("rvc", "#{username}@#{hostname}" , password ) unless 
        keychain["rvc", "#{username}@#{hostname}" ] == password
    end
  else
    return false
  end
end


def check_known_hosts host, peer_public_key
  known_hosts = RVC::KnownHosts.new
  result, arg = known_hosts.verify 'vim', host, peer_public_key.to_s

  if result == :not_found
    puts "The authenticity of host '#{host}' can't be established."
    puts "Public key fingerprint is #{arg}."
    err "Connection failed" unless agree("Are you sure you want to continue connecting (y/n)? ", true)
    puts "Warning: Permanently added '#{host}' (vim) to the list of known hosts"
    known_hosts.add 'vim', host, peer_public_key.to_s
  elsif result == :mismatch
    err "Public key fingerprint for host '#{host}' does not match #{known_hosts.filename}:#{arg}."
  elsif result == :ok
  else
    err "Unexpected result from known_hosts check"
  end
end


opts :tasks do
  summary "Watch tasks in progress"
end

def tasks
  conn = single_connection [shell.fs.cur]

  begin
    view = conn.serviceContent.viewManager.CreateListView

    collector = conn.serviceContent.taskManager.CreateCollectorForTasks(:filter => {
      :time => {
        :beginTime => conn.serviceInstance.CurrentTime.to_datetime, # XXX
        :timeType => :queuedTime
      }
    })
    collector.SetCollectorPageSize :maxCount => 1

    filter_spec = {
      :objectSet => [
        {
          :obj => view,
          :skip => true,
          :selectSet => [
            VIM::TraversalSpec(:path => 'view', :type => view.class.wsdl_name)
          ]
        },
        { :obj => collector },
      ],
      :propSet => [
        { :type => 'Task', :pathSet => %w(info.state) },
        { :type => 'TaskHistoryCollector', :pathSet => %w(latestPage) },
      ]
    }
    filter = conn.propertyCollector.CreateFilter(:partialUpdates => false, :spec => filter_spec)

    ver = ''
    loop do
      result = conn.propertyCollector.WaitForUpdates(:version => ver)
      ver = result.version
      result.filterSet[0].objectSet.each do |r|
        remove = []
        case r.obj
        when VIM::TaskHistoryCollector
          infos = collector.ReadNextTasks :maxCount => 100
          view.ModifyListView :add => infos.map(&:task)
        when VIM::Task
          puts "#{Time.now} #{r.obj.info.name} #{r.obj.info.entityName} #{r['info.state']}" unless r['info.state'] == nil
          remove << r.obj if %w(error success).member? r['info.state']
        end
        view.ModifyListView :remove => remove unless remove.empty?
      end
    end
  rescue Interrupt
  ensure
    filter.DestroyPropertyFilter if filter
    collector.DestroyCollector if collector
    view.DestroyView if view
  end
end



