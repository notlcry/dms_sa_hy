class DmsVmomi::VIM::Service 
  def ls_text r
    " (datacenter)"
  end

  def children
    vmFolder, datastoreFolder, networkFolder, hostFolder =
      collect *%w(vmFolder datastoreFolder networkFolder hostFolder)
    {
      'vms' => vmFolder,
      'datastores' => datastoreFolder,
      'networks' => networkFolder,
      'computers' => hostFolder,
    }
  end

  # For compatibility with previous RVC versions
  def traverse_one arc
    children = self.rvc_children
    return children[arc] if children.member? arc
    if arc == 'vm' then return vmFolder
    elsif arc == 'datastore' then return datastoreFolder
    elsif arc == 'network' then return networkFolder
    elsif arc == 'host' then return hostFolder
    end
  end

  def self.folder?
    true
  end
end