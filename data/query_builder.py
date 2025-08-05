
def build_query(fecha_ini, fecha_fin):
    with open("sql/base_query.sql", "r") as f:
        base_query = f.read()
    filtro = f"\nWHERE a.pri_action_date BETWEEN TO_DATE('{fecha_ini.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS') AND TO_DATE('{fecha_fin.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS')"
    return base_query + filtro
