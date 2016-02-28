from py2xml import Py2XML
import yaml


class Job(object):
  """
      <joblist>
      <job>
        <description>sdafafasfadfa</description>
        <dispatch>
          <excludePrecedence>true</excludePrecedence>
          <keepgoing>false</keepgoing>
          <rankOrder>ascending</rankOrder>
          <threadcount>1</threadcount>
        </dispatch>
        <executionEnabled>true</executionEnabled>
        <group>haoyan</group>
        <id>d436e04c-6515-4ab3-838e-a6465218f001</id>
        <loglevel>INFO</loglevel>
        <name>test</name>
        <nodefilters>
          <filter>name:10.74.125.195 name:10.74.125.196</filter>
        </nodefilters>
        <nodesSelectedByDefault>true</nodesSelectedByDefault>
        <scheduleEnabled>true</scheduleEnabled>
        <sequence keepgoing='false' strategy='node-first'>
          <command>
            <description>test command</description>
            <exec>whoami</exec>
          </command>
          <command>
            <description>just for restart collectd </description>
            <script><![CDATA[mv /tmp/collectd/conf /opt/collectd/etc/config
            ps -ef | grep collectd | awk "{print $4}" | kill -9
            /opt/collect/bin start]]></script>
            <scriptargs />
            <scriptinterpreter>sudo</scriptinterpreter>
          </command>
          <command>
            <description>just for test</description>
            <node-step-plugin type='copyfile'>
              <configuration>
                <entry key='destinationPath' value='/tmp/safsdf' />
                <entry key='echo' value='true' />
                <entry key='sourcePath' value='/tmp/xxx' />
              </configuration>
            </node-step-plugin>
          </command>
        </sequence>
        <uuid>d436e04c-6515-4ab3-838e-a6465218f001</uuid>
      </job>
    </joblist>
  """

  def __init__(self,keepgoing='true',strategy='node-first'):
    self.sequence_key = "sequence keepgoing='%s' strategy='%s'" % (keepgoing,strategy)
    self.definition = {
        'joblist':[{
                "description":[],
                "executionEnabled":['true'],
                "group": [],
                "id": [],
                "loglevel": ["INFO"],
                "name": [],
                "scheduleEnabled": ["true"],
                "dispatch": [{"excludePrecedence":["true"],"keepgoing":["false"],"rankOrder":["ascending"],"threadcount":["1"]}],
                "nodefilters":{"filter":[]},
                "uuid":["fd026e9e-8be4-469e-b732-8d9605f7c57e"]
                }]
     }
    self.definition['joblist'][0][self.sequence_key] = []

  def _addsequence(self,dict):
    self.definition['joblist'][0][self.sequence_key].append(dict)

  def addcopyfile(self,src,dst):
    dict = {'node-step-plugin': {"type": "copyfile","configuration":[{"key":"destinationPath","value":dst},{"key":"echo","value":"true"},{"key":"sourcePath","value":src}]}}
    self._addsequence(dict)
 
  def addcommand(self,cmd):
    dict = {"exec": cmd}
    self._addsequence(dict)

  def addlocalcommand(self,cmd):
    dict = {'node-step-plugin': {"type": "localexec","configuration":[{"key":"command","value":cmd}]}}
    self._addsequence(dict)

  def setdesc(self,desp):
    self.definition['joblist'][0]['description'].append(desp)

  def setName(self,name):
    self.definition['joblist'][0]['name'].append(name)

  def setGroup(self,name):
    self.definition['joblist'][0]['group'].append(name)

  def setNodeFilter(self,ip):
    """

    :param name: name:10.74.125.x name:10.x.x.x
    :return:
    """
    filter = "name:%s" % ip
    self.definition['joblist'][0]['nodefilters']['filter'].append(filter)

  def setuuid(self,uuid):
    self.definition['joblist'][0]["uuid"] = uuid
  
  def to_xml(self):
    serializer = Py2XML()
    xml_string = serializer.parse( self.definition )
    return xml_string
  



