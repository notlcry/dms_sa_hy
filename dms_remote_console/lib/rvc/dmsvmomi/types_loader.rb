require 'set'
require 'monitor'

module DmsVmomi
class TypeLoader
	def initialize basic_dirs,extension_dirs,namespace
		@basic = basic_dirs
		@db = []
		@extension_dirs = extension_dirs
		@namespace = namespace 
		@lock = Monitor.new
		preload
	end

	def preload
		Dir.open(@basic) do |dir|
		  dir.each do |file|
		  	next unless file =~ /\.rb$/
		  	file_path = File.join(dir,file)
		  	@db << file
		    puts "loadfile #{file}"
		  	load file_path
		  end
		end
	end

	def reload_extensions
      @extension_dirs.each do |path|
        reload_extensions_dir path
      end
    end

    def reload_extensions_dir path
      Dir.open(path) do |dir|
        dir.each do |file|
	        next unless file =~ /\.rb$/
	        file_path = File.join(dir, file)
	        if @db.member? file
	        	puts "loadfile #{file}"
	        	load file_path
	        end
	    end
      end
    end

  end
end