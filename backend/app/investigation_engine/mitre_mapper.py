from typing import List, Dict

class MitreMapper:
    """Maps DeceptionAction types to MITRE ATT&CK techniques."""
    
    MAPPING = {
        "DIRECTORY_SCAN": {"id": "T1083", "name": "File and Directory Discovery"},
        "VIEW_ENV_LEAK": {"id": "T1552.001", "name": "Credentials In Files"},
        "AUTH_FAILURE": {"id": "T1110", "name": "Brute Force"},
        "WP_AUTH_ATTEMPT": {"id": "T1110.001", "name": "Password Guessing"},
        "DB_AUTH_ATTEMPT": {"id": "T1110.001", "name": "Password Guessing"},
        "FILE_UPLOAD_ATTEMPT": {"id": "T1505.003", "name": "Web Shell"},
        "EXPORT_DATA": {"id": "T1005", "name": "Data from Local System"},
        "HONEY_TOKEN_TRIGGERED": {"id": "T1528", "name": "Steal Application Access Token"},
        "SQLI_ATTEMPT": {"id": "T1190", "name": "Exploit Public-Facing Application"},
        "SCAN": {"id": "T1595.002", "name": "Vulnerability Scanning"}
    }

    @staticmethod
    def map_actions(actions: List[str]) -> Dict[str, str]:
        """Returns a unique dictionary of MITRE techniques triggered."""
        mitre_results = {}
        for action in actions:
            if action in MitreMapper.MAPPING:
                technique = MitreMapper.MAPPING[action]
                mitre_results[technique["id"]] = technique["name"]
        return mitre_results
