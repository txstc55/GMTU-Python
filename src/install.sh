pip install -e .
fcm_token=$(cat fcm_token)
fcm_token=$(< fcm_token)
fcm_token=${fcm_token//$'\n'/}
fcm_token=${fcm_token//$'\r'/}
gmtu --fcm-token $fcm_token --content "GMTU Python compiled"
