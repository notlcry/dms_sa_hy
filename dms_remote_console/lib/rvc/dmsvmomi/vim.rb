module DmsVmomi
class VIM < Connection
	def self.connect opts
		fail unless opts.is_a? Hash
		new(opts)
	end

	def rootFolder
		@rootFolder ||= VIM::RootFolder.new(self)
	end
    load_vmodl(File.join(File.dirname(__FILE__), "vim"))
end

end