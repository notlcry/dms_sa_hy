# encoding: utf-8
require "logstash/filters/base"
require "logstash/namespace"
require "zookeeper"
require "logstash/json"
require "logstash/timestamp"

# This is Zookeeper filter based on one specific model(two-level hashmap), just like(accountId/ip(json properties))
class LogStash::Filters::Zookeeper < LogStash::Filters::Base

  config_name "zookeeper"

  config :source, :validate => :string, :required => true

  config :target, :validate => :string, :required => true

  config :zk_address, :validate => :string, :default => "127.0.0.1:2181"

  config :zk_path, :validate => :string, :required => true

  config :groupname,:valdiate=> :string, :required => true

  config :propertykey, :validate => :string, :required => true

  config :refresh_interval, :validate => :number, :default => 300

  JSONPARSEFAILURE_TAG = "_jsonparsefailure"
  
  public
  def register
    @client = Zookeeper.new(@zk_address)

    @mapping=Hash.new 

    @next_refresh = Time.now + @refresh_interval

    loadInventory

  end # def register

  public
  def filter(event)
    return unless filter?(event)

    @logger.debug("Running zookeeper filter", :event => event)

    return unless event.include?(@source)

    return unless event.include?(@groupname)

    if  @next_refresh < Time.now
      loadInventory
      @next_refresh = Time.now + @refresh_interval
    end

    source = event[@source]

    group = event[@groupname]

     if @mapping.include?(group) and @mapping[group].include?(source)
         event[@target] = @mapping[group][source]
     else
         event[@target] = "Unknown"
     end
       


    @logger.debug("Event after json filter", :event => event)

  end # def filter

  def loadInventory()
      begin
        znode = @client.get_children({:path =>@zk_path})
        if znode[:stat].exists
          first_keys = znode[:children]
          @mapping["first_keys"] = first_keys
          for key in first_keys
            if not @mapping.include?key
              @mapping[key] = Hash.new 
            end
            key_path = File.join(@zk_path,key)
            itemnode = @client.get_children({:path => key_path})
            if itemnode[:stat].exists
              items = itemnode[:children]
              @logger.error(items)
              for item in items 
                item_path = File.join(key_path,item)
                if raw != nil
                   begin
                     parsed = LogStash::Json.load(raw)
                   rescue => e
                     @logger.warn("Error parsing json", :source => @source, :raw => raw, :exception => e)
                     return
                   end
                  @mapping[key][item] =  parsed[@propertykey]
                end
              end
            end
          end
        end              
      rescue Exception => e
         @logger.error("load loadInventory Exception",:event => e)
      end
  end

end # class LogStash::Filters::Zookeeper/
