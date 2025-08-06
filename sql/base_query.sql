-- Consulta base (adaptada del archivo original)
SELECT a.*
FROM swp_provisioning_interfaces a
WHERE a.pri_action_date BETWEEN :fecha_ini AND :fecha_fin
:ne_id
:action
