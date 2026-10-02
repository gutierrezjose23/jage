-- Selecciona la base jage_local en MySQL Workbench antes de ejecutar.
-- Consultas de lectura: no modifican datos ni muestran contraseñas.

SELECT u.id,
       u.first_name AS nombre,
       u.last_name AS apellido,
       u.phone AS telefono,
       c.dni,
       u.email AS correo
FROM clientes AS c
INNER JOIN users AS u ON u.id = c.user_id
WHERE u.role = 'passenger'
ORDER BY u.id;

SELECT u.id,
       u.first_name AS nombre,
       u.last_name AS apellido,
       u.phone AS telefono,
       c.dni,
       u.email AS correo,
       c.placa
FROM conductores AS c
INNER JOIN users AS u ON u.id = c.user_id
WHERE u.role = 'driver'
ORDER BY u.id;
