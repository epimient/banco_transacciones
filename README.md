# Sistema bancario: CRUD y transacciones con Python y SQLite

> **Asignatura:** Acceso a Datos  
> **Semana 10:** CRUD, transacciones y manejo de excepciones  
> **Tipo de proyecto:** Aplicación de consola con fines educativos

## Descripción

Este proyecto amplía el ejemplo trabajado en clase con la base de datos `banco_demo.db` y la tabla `cuentas`. El ejemplo inicial registraba a Juan y María y realizaba una transferencia de dinero mediante dos instrucciones `UPDATE`. Ahora se convierte en una aplicación de consola con un menú, operaciones CRUD, validaciones y manejo de transacciones.

Se utilizan **funciones, `while`, `if/elif`, SQL, `try/except`, `commit()` y `rollback()`**. No se implementan clases, patrones DAO ni ORM: el propósito es comprender el acceso directo a SQLite desde Python.

**Objetivo de aprendizaje:** desarrollar un CRUD funcional y comprender por qué las modificaciones relacionadas deben confirmarse o revertirse como una sola unidad de trabajo.

## Requisitos

- Python 3.8 o superior.
- Módulo `sqlite3`, incluido en la biblioteca estándar de Python.
- Terminal para ejecutar el programa.

No es necesario instalar paquetes mediante `pip`.

## Archivos del proyecto

```text
banco_crud/
├── README.md          # Documentación del proyecto
├── banco.py           # Aplicación de consola
└── banco_demo.db      # Se crea automáticamente al iniciar
```

El archivo `banco_demo.db` no se entrega vacío: se crea automáticamente cuando se ejecuta `banco.py` por primera vez. Si la base de datos ya existe, el programa conserva los registros que contiene.

## Ejecutar la aplicación

En una terminal, desde la carpeta del proyecto:

```bash
python banco.py
```

En algunos sistemas el intérprete se invoca con:

```bash
python3 banco.py
```

Al iniciar aparece el menú:

```text
===== SISTEMA BANCARIO =====
1. Crear cuenta
2. Ver todas las cuentas
3. Buscar cuenta por ID
4. Actualizar titular
5. Eliminar cuenta
6. Consignar dinero
7. Retirar dinero
8. Transferir dinero
9. Salir
Seleccione una opcion:
```

**Primer uso recomendado:** registrar dos cuentas mediante la opción `1`: Juan con saldo `1000` y María con saldo `500`. Después consultar sus identificadores con la opción `2`. Los IDs pueden ser distintos de `1` y `2` si la base de datos contiene registros anteriores.

## Estructura de la base de datos

Al iniciar se ejecuta:

```sql
CREATE TABLE IF NOT EXISTS cuentas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    saldo REAL NOT NULL CHECK (saldo >= 0)
);
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Identificador automático y único de la cuenta. |
| `nombre` | `TEXT NOT NULL` | Nombre del titular. |
| `saldo` | `REAL NOT NULL CHECK (saldo >= 0)` | Saldo de la cuenta, que no puede ser negativo. |

`CREATE TABLE IF NOT EXISTS` evita intentar crear de nuevo una tabla existente; **no elimina ni reinicia** los datos ya almacenados.

> **Nota técnica:** se mantiene `REAL` para dar continuidad al ejercicio de clase. La representación con coma flotante puede producir problemas de precisión en operaciones monetarias. Este ejemplo **no es adecuado para un banco real**: un sistema financiero requeriría cantidades exactas, autenticación, permisos, auditoría y controles adicionales.

## Funcionalidades

| Opción | Función de Python | SQL principal | ¿Modifica datos? |
|---|---|---|---|
| 1. Crear cuenta | `crear_cuenta()` | `INSERT` | Sí |
| 2. Ver cuentas | `mostrar_cuentas()` | `SELECT` | No |
| 3. Buscar cuenta | `buscar_cuenta()` | `SELECT ... WHERE` | No |
| 4. Actualizar titular | `actualizar_titular()` | `UPDATE` | Sí |
| 5. Eliminar cuenta | `eliminar_cuenta()` | `DELETE` | Sí |
| 6. Consignar | `consignar()` | `UPDATE` | Sí |
| 7. Retirar | `retirar()` | `UPDATE` | Sí |
| 8. Transferir | `transferir()` | Dos `UPDATE` | Sí |
| 9. Salir | `menu()` | — | No |

### Crear una cuenta

Solicita un nombre y saldo inicial. Rechaza nombres vacíos, importes negativos y números inválidos. Ejecuta una consulta parametrizada:

```python
cursor = conexion.execute(
    "INSERT INTO cuentas (nombre, saldo) VALUES (?, ?)",
    (nombre, saldo)
)
conexion.commit()
print(cursor.lastrowid)
```

El signo `?` representa un parámetro: los datos del usuario se envían por separado del texto SQL. `cursor.lastrowid` permite conocer el ID generado por SQLite para la cuenta recién creada.

### Mostrar y buscar cuentas

Para listar todas las cuentas:

```python
cuentas = conexion.execute(
    "SELECT id, nombre, saldo FROM cuentas ORDER BY id"
).fetchall()
```

`fetchall()` devuelve las filas del resultado. Para buscar solamente una cuenta por su clave primaria se emplea `fetchone()`:

```python
cuenta = conexion.execute(
    "SELECT id, nombre, saldo FROM cuentas WHERE id = ?",
    (id_cuenta,)
).fetchone()
```

Si no existe, `fetchone()` devuelve `None`.

### Actualizar el titular

Utiliza `UPDATE ... WHERE id = ?`. Antes de modificar, valida que el ID sea un entero positivo y que el nombre no esté vacío. Si ninguna fila coincide con el ID, informa que la cuenta no existe.

### Eliminar una cuenta

Antes de eliminar, se comprueba que la cuenta exista, que su saldo sea `0` y que el usuario confirme la eliminación. Como protección adicional, el `DELETE` incluye `AND saldo = 0`.

**Limitación educativa:** en sistemas financieros reales se conservaría un historial de operaciones y normalmente no se borraría físicamente una cuenta como en este ejercicio.

### Consignar dinero

Agrega un monto positivo al saldo de la cuenta seleccionada:

```sql
UPDATE cuentas
SET saldo = saldo + ?
WHERE id = ?;
```

### Retirar dinero

Descuenta el monto **solo si existe la cuenta y tiene saldo suficiente**:

```sql
UPDATE cuentas
SET saldo = saldo - ?
WHERE id = ? AND saldo >= ?;
```

El programa comprueba `cursor.rowcount` para saber si la instrucción afectó una fila. Si devuelve `0`, la cuenta no existe o su saldo no permite el retiro.

## ¿Qué es una transacción y por qué la necesitamos?

Una **transacción** es una unidad lógica de trabajo que agrupa una o varias operaciones de base de datos. Una transferencia debe descontar dinero de una cuenta **y** acreditarlo en otra. No sería correcto confirmar solo una de las dos modificaciones.

Supongamos estas cuentas:

| ID | Titular | Saldo antes | Saldo después de transferir $200 |
|---:|---|---:|---:|
| 1 | Juan | $1.000 | $800 |
| 2 | María | $500 | $700 |

La operación utiliza dos instrucciones:

```sql
UPDATE cuentas SET saldo = saldo - 200 WHERE id = 1;
UPDATE cuentas SET saldo = saldo + 200 WHERE id = 2;
```

Si ocurre un fallo entre ambas, no debemos conservar el descuento sin la acreditación correspondiente.

- **`commit()`** confirma los cambios pendientes de la transacción.
- **`rollback()`** revierte los cambios pendientes de la transacción.

En este proyecto se utiliza el control transaccional habitual de `sqlite3`, además de un `BEGIN IMMEDIATE` explícito en la transferencia. Este último solicita el acceso de escritura al inicio de la operación; el propósito es evitar ejecutar la validación del destino y el descuento como pasos desconectados de la misma transacción de escritura.

### Transferencia en Python

La función `transferir()` sigue este orden:

1. Solicita los IDs de origen y destino, y el monto.
2. Valida que el monto sea positivo y que las cuentas sean diferentes.
3. Inicia una transacción de escritura con `BEGIN IMMEDIATE`.
4. Comprueba que la cuenta de destino exista.
5. Descuenta al origen, siempre que tenga suficiente saldo.
6. Comprueba que el descuento haya afectado exactamente una fila.
7. Acredita el dinero al destino.
8. Confirma con `commit()` si ambas modificaciones terminaron correctamente.
9. Si ocurre una excepción, ejecuta `rollback()` para revertir las modificaciones pendientes.

Fragmento representativo del manejo de errores:

```python
try:
    conexion.execute("BEGIN IMMEDIATE")
    # Verificar destino, descontar y acreditar...
    conexion.commit()
except (ValueError, RuntimeError, sqlite3.Error) as error:
    conexion.rollback()
    print("Transferencia cancelada:", error)
finally:
    conexion.close()
```

### `try`, `except` y `finally`

| Elemento | Responsabilidad |
|---|---|
| `try` | Ejecutar operaciones que pueden fallar. |
| `except` | Capturar y gestionar determinados errores. |
| `rollback()` | Revertir las modificaciones pendientes si la operación debe cancelarse. |
| `finally` | Cerrar la conexión aunque ocurra un error. |

`try/except` **no reemplaza** las transacciones. Controla errores de Python; `commit()` y `rollback()` controlan la confirmación o reversión de modificaciones en SQLite.

### ¿Qué es `cursor.rowcount`?

Es un atributo que indica la cantidad de filas afectadas por una instrucción como `UPDATE` o `DELETE`.

```python
cursor = conexion.execute(
    "UPDATE cuentas SET saldo = saldo - ? WHERE id = ? AND saldo >= ?",
    (monto, origen, monto)
)
if cursor.rowcount != 1:
    raise ValueError("Cuenta origen inexistente o saldo insuficiente")
```

- `rowcount == 1`: se afectó la cuenta esperada.
- `rowcount == 0`: no se encontró una cuenta que cumpliera la condición.

**Importante:** una instrucción `UPDATE` que afecta cero filas no tiene por qué generar una excepción de SQLite. Por eso se verifica el resultado y, si es necesario, se genera un error mediante `raise`.

## Laboratorio: comprobar `rollback()`

Esta prueba se realiza **después** de crear las cuentas y verificar sus IDs desde el menú.

### Prueba A — Transferencia correcta

1. Registrar a Juan con `$1.000` y María con `$500`, si aún no existen.
2. Identificar sus IDs usando **Ver todas las cuentas**.
3. Seleccionar **8. Transferir dinero**.
4. Transferir `$200` desde Juan hacia María.
5. Consultar nuevamente los saldos.

Resultado esperado: Juan `$800`, María `$700`.

### Prueba B — Error simulado

En `banco.py`, la función `transferir()` contiene el siguiente fragmento:

```python
if simular_error:
    raise RuntimeError("Error simulado en transferencia")
```

Para realizar la prueba desde el menú, cambia temporalmente esta línea en `menu()`:

```python
elif opcion == '8': transferir()
```

por:

```python
elif opcion == '8': transferir(simular_error=True)
```

Después:

1. Ejecuta nuevamente el programa.
2. Intenta transferir `$100` entre las dos cuentas.
3. Observa el mensaje `Transferencia cancelada: Error simulado en transferencia`.
4. Consulta de nuevo los saldos.

**Resultado esperado:** Juan conserva `$800` y María `$700`. El descuento realizado antes del error fue revertido mediante `rollback()`.

Restablece `transferir()` sin el argumento `simular_error=True` al terminar el laboratorio.

> **Atención:** si ejecutas otras transacciones entre estas pruebas, los saldos reales pueden cambiar. Lo importante es comparar el estado inmediatamente anterior al fallo con el estado posterior al `rollback()`.

## Validaciones implementadas

| Situación | Comportamiento esperado |
|---|---|
| Nombre vacío o compuesto solo por espacios | Rechazar la creación o actualización. |
| Saldo inicial negativo | Rechazar. |
| Monto no numérico, infinito o `NaN` | Rechazar. |
| Monto de retiro, consignación o transferencia igual a cero | Rechazar. |
| ID no numérico o no positivo | Rechazar. |
| ID inexistente | Informar que la cuenta no existe. |
| Retiro superior al saldo | No modificar el saldo. |
| Transferencia a la misma cuenta | Rechazar. |
| Transferencia sin fondos suficientes | Cancelar sin modificar las cuentas. |
| Eliminar cuenta con saldo diferente de cero | Rechazar. |
| Eliminar cuenta sin confirmación | Cancelar la operación. |
| Error durante la transferencia | Ejecutar `rollback()` y conservar el estado previo. |

## Retos para los estudiantes

Una vez que la aplicación funcione, desarrolla las siguientes mejoras **sin modificar el comportamiento correcto de las transacciones existentes**.

### Reto 1 — Historial de movimientos

Crea una tabla `movimientos` para registrar consignaciones, retiros y transferencias. Cada registro debe incluir un identificador, tipo de movimiento, monto y cuentas involucradas cuando corresponda.

En una transferencia, el registro del movimiento y las modificaciones de saldos deberán pertenecer a la **misma transacción**.

### Reto 2 — Límite de retiro

Impide retirar más de `$1.000.000` en una sola operación y presenta un mensaje específico cuando se supere ese límite.

### Reto 3 — Comisión por transferencia

Agrega una comisión fija de `$2.000` a cada transferencia. El saldo de origen debe ser suficiente para cubrir **monto + comisión**. Define y documenta qué representa contablemente la comisión, evitando que se pierda o se cree dinero sin un registro adecuado.

### Reto 4 — Simulación y evidencia de rollback

Provoca una excepción después de descontar y antes de acreditar. Muestra las cuentas **antes y después** de la operación fallida mediante `SELECT`, y explica por qué los saldos permanecen sin cambios.

## Limitaciones y posibles mejoras

Este proyecto es un **prototipo educativo**, no un sistema bancario de producción. Entre las mejoras profesionales se encuentran: aritmética monetaria exacta, autenticación, autorización, trazabilidad y auditoría inmutable, reglas de negocio completas, pruebas automatizadas, control de operaciones repetidas y políticas de manejo de errores y concurrencia.

## Referencias

- [Documentación oficial de `sqlite3` en Python](https://docs.python.org/3/library/sqlite3.html)
- [Transacciones en SQLite](https://www.sqlite.org/lang_transaction.html)
- [Restricciones `CHECK` en SQLite](https://www.sqlite.org/lang_createtable.html#check_constraints)

---

**Conclusión:** el CRUD administra los registros; las transacciones permiten controlar conjuntos de modificaciones que deben confirmarse o revertirse como una unidad. Junto con validaciones y manejo de excepciones, estas herramientas son la base para desarrollar aplicaciones de acceso a datos más confiables.
