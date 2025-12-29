import { AttackMatrixData } from '@/types';

// 模拟ATT&CK矩阵数据
export const mockAttackMatrixData: AttackMatrixData[] = [
  // Initial Access
  {
    technique_id: 'T1190',
    technique_name: 'Exploit Public-Facing Application',
    tactic_name: 'Initial Access',
    function_count: 5
  },
  {
    technique_id: 'T1078',
    technique_name: 'Valid Accounts',
    tactic_name: 'Initial Access',
    function_count: 3
  },
  // Execution
  {
    technique_id: 'T1059',
    technique_name: 'Command and Scripting Interpreter',
    tactic_name: 'Execution',
    function_count: 8
  },
  {
    technique_id: 'T1055',
    technique_name: 'Process Injection',
    tactic_name: 'Execution',
    function_count: 12
  },
  {
    technique_id: 'T1053',
    technique_name: 'Scheduled Task/Job',
    tactic_name: 'Execution',
    function_count: 4
  },
  // Persistence
  {
    technique_id: 'T1547',
    technique_name: 'Boot or Logon Autostart Execution',
    tactic_name: 'Persistence',
    function_count: 6
  },
  {
    technique_id: 'T1053',
    technique_name: 'Scheduled Task/Job',
    tactic_name: 'Persistence',
    function_count: 4
  },
  // Privilege Escalation
  {
    technique_id: 'T1068',
    technique_name: 'Exploitation for Privilege Escalation',
    tactic_name: 'Privilege Escalation',
    function_count: 7
  },
  {
    technique_id: 'T1055',
    technique_name: 'Process Injection',
    tactic_name: 'Privilege Escalation',
    function_count: 10
  },
  // Defense Evasion
  {
    technique_id: 'T1027',
    technique_name: 'Obfuscated Files or Information',
    tactic_name: 'Defense Evasion',
    function_count: 15
  },
  {
    technique_id: 'T1140',
    technique_name: 'Deobfuscate/Decode Files or Information',
    tactic_name: 'Defense Evasion',
    function_count: 9
  },
  {
    technique_id: 'T1112',
    technique_name: 'Modify Registry',
    tactic_name: 'Defense Evasion',
    function_count: 6
  },
  // Credential Access
  {
    technique_id: 'T1003',
    technique_name: 'OS Credential Dumping',
    tactic_name: 'Credential Access',
    function_count: 11
  },
  {
    technique_id: 'T1056',
    technique_name: 'Input Capture',
    tactic_name: 'Credential Access',
    function_count: 5
  },
  // Discovery
  {
    technique_id: 'T1082',
    technique_name: 'System Information Discovery',
    tactic_name: 'Discovery',
    function_count: 8
  },
  {
    technique_id: 'T1018',
    technique_name: 'Remote System Discovery',
    tactic_name: 'Discovery',
    function_count: 4
  },
  // Lateral Movement
  {
    technique_id: 'T1021',
    technique_name: 'Remote Services',
    tactic_name: 'Lateral Movement',
    function_count: 7
  },
  {
    technique_id: 'T1570',
    technique_name: 'Lateral Tool Transfer',
    tactic_name: 'Lateral Movement',
    function_count: 3
  },
  // Collection
  {
    technique_id: 'T1113',
    technique_name: 'Screen Capture',
    tactic_name: 'Collection',
    function_count: 5
  },
  {
    technique_id: 'T1115',
    technique_name: 'Clipboard Data',
    tactic_name: 'Collection',
    function_count: 2
  },
  // Command and Control
  {
    technique_id: 'T1071',
    technique_name: 'Application Layer Protocol',
    tactic_name: 'Command & Control',
    function_count: 9
  },
  {
    technique_id: 'T1090',
    technique_name: 'Proxy',
    tactic_name: 'Command & Control',
    function_count: 6
  },
  // Impact
  {
    technique_id: 'T1490',
    technique_name: 'Inhibit System Recovery',
    tactic_name: 'Impact',
    function_count: 4
  },
  {
    technique_id: 'T1485',
    technique_name: 'Data Destruction',
    tactic_name: 'Impact',
    function_count: 7
  }
];