LIST_PROVISIONING = """
SELECT * FROM provisioning_interface
WHERE 1=1
    {msisdn_filter}
    {status_filter}
    {error_filter}
    {ne_service_filter}
    {date_filter}
ORDER BY {order_column} {order_dir}
"""

DETAIL_PROVISIONING = "SELECT * FROM provisioning_interface WHERE pri_id = :pri_id"

STATS_PROVISIONING = """
SELECT {group_by} as group_key, COUNT(*) as total
FROM provisioning_interface
WHERE pri_action_date BETWEEN :from AND :to
GROUP BY {group_by}
"""
