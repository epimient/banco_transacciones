import math
import sqlite3

DB = 'banco_demo.db'


def crear_bd():
    conexion = sqlite3.connect(DB)
    try:
        conexion.execute('''
            CREATE TABLE IF NOT EXISTS cuentas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                saldo REAL NOT NULL CHECK (saldo >= 0)
            )
        ''')
        conexion.commit()
    finally:
        conexion.close()


def leer_monto(mensaje, permite_cero=False):
    try:
        monto = float(input(mensaje))
    except ValueError:
        print('Error: ingrese un numero valido')
        return None
    if not math.isfinite(monto) or monto < 0 or (not permite_cero and monto == 0):
        print('Error: ingrese un monto valido y ' + ('no negativo' if permite_cero else 'positivo'))
        return None
    return monto


def leer_id(mensaje):
    try:
        identificador = int(input(mensaje))
        if identificador <= 0:
            raise ValueError
        return identificador
    except ValueError:
        print('Error: el ID debe ser un entero positivo')
        return None


def crear_cuenta():
    nombre = input('Nombre del titular: ').strip()
    if not nombre:
        print('Error: el nombre no puede estar vacio')
        return
    saldo = leer_monto('Saldo inicial: ', permite_cero=True)
    if saldo is None:
        return
    conexion = sqlite3.connect(DB)
    try:
        cursor = conexion.execute('INSERT INTO cuentas (nombre, saldo) VALUES (?, ?)', (nombre, saldo))
        conexion.commit()
        print(f'Cuenta creada. ID: {cursor.lastrowid}')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error al crear cuenta:', error)
    finally:
        conexion.close()


def mostrar_cuentas():
    conexion = sqlite3.connect(DB)
    try:
        cuentas = conexion.execute('SELECT id, nombre, saldo FROM cuentas ORDER BY id').fetchall()
        if not cuentas:
            print('No hay cuentas registradas')
        for identificador, nombre, saldo in cuentas:
            print(f'ID: {identificador} | Titular: {nombre} | Saldo: ${saldo:.2f}')
    except sqlite3.Error as error:
        print('Error al consultar:', error)
    finally:
        conexion.close()


def buscar_cuenta():
    identificador = leer_id('ID de la cuenta: ')
    if identificador is None:
        return
    conexion = sqlite3.connect(DB)
    try:
        cuenta = conexion.execute('SELECT id, nombre, saldo FROM cuentas WHERE id = ?', (identificador,)).fetchone()
        if cuenta is None:
            print('La cuenta no existe')
        else:
            print(f'ID: {cuenta[0]} | Titular: {cuenta[1]} | Saldo: ${cuenta[2]:.2f}')
    except sqlite3.Error as error:
        print('Error al buscar:', error)
    finally:
        conexion.close()


def actualizar_titular():
    identificador = leer_id('ID de la cuenta: ')
    if identificador is None:
        return
    nombre = input('Nuevo titular: ').strip()
    if not nombre:
        print('Error: el nombre no puede estar vacio')
        return
    conexion = sqlite3.connect(DB)
    try:
        cursor = conexion.execute('UPDATE cuentas SET nombre = ? WHERE id = ?', (nombre, identificador))
        if cursor.rowcount == 0:
            conexion.rollback()
            print('La cuenta no existe')
        else:
            conexion.commit()
            print('Titular actualizado')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error al actualizar:', error)
    finally:
        conexion.close()


def eliminar_cuenta():
    identificador = leer_id('ID de la cuenta: ')
    if identificador is None:
        return
    conexion = sqlite3.connect(DB)
    try:
        cuenta = conexion.execute('SELECT nombre, saldo FROM cuentas WHERE id = ?', (identificador,)).fetchone()
        if cuenta is None:
            print('La cuenta no existe')
            return
        if cuenta[1] != 0:
            print('No se puede eliminar una cuenta con saldo')
            return
        confirmacion = input(f'Eliminar cuenta de {cuenta[0]}? (s/n): ').strip().lower()
        if confirmacion != 's':
            print('Eliminacion cancelada')
            return
        cursor = conexion.execute('DELETE FROM cuentas WHERE id = ? AND saldo = 0', (identificador,))
        if cursor.rowcount == 0:
            conexion.rollback()
            print('No se pudo eliminar la cuenta')
        else:
            conexion.commit()
            print('Cuenta eliminada')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error al eliminar:', error)
    finally:
        conexion.close()


def consignar():
    identificador = leer_id('ID de la cuenta: ')
    if identificador is None:
        return
    monto = leer_monto('Cantidad a consignar: ')
    if monto is None:
        return
    conexion = sqlite3.connect(DB)
    try:
        cursor = conexion.execute('UPDATE cuentas SET saldo = saldo + ? WHERE id = ?', (monto, identificador))
        if cursor.rowcount == 0:
            conexion.rollback()
            print('La cuenta no existe')
        else:
            conexion.commit()
            print('Consignacion exitosa')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error:', error)
    finally:
        conexion.close()


def retirar():
    identificador = leer_id('ID de la cuenta: ')
    if identificador is None:
        return
    monto = leer_monto('Cantidad a retirar: ')
    if monto is None:
        return
    conexion = sqlite3.connect(DB)
    try:
        cursor = conexion.execute('UPDATE cuentas SET saldo = saldo - ? WHERE id = ? AND saldo >= ?', (monto, identificador, monto))
        if cursor.rowcount == 0:
            conexion.rollback()
            print('Cuenta inexistente o saldo insuficiente')
        else:
            conexion.commit()
            print('Retiro exitoso')
    except sqlite3.Error as error:
        conexion.rollback()
        print('Error:', error)
    finally:
        conexion.close()


def transferir(simular_error=False):
    origen = leer_id('ID de cuenta origen: ')
    if origen is None:
        return
    destino = leer_id('ID de cuenta destino: ')
    if destino is None:
        return
    monto = leer_monto('Monto a transferir: ')
    if monto is None:
        return
    if origen == destino:
        print('No puede transferir a la misma cuenta')
        return
    conexion = sqlite3.connect(DB)
    try:
        # Se solicita el bloqueo de escritura antes de verificar el destino.
        conexion.execute('BEGIN IMMEDIATE')
        existe_destino = conexion.execute('SELECT id FROM cuentas WHERE id = ?', (destino,)).fetchone()
        if existe_destino is None:
            raise ValueError('Cuenta destino inexistente')
        cursor = conexion.execute(
            'UPDATE cuentas SET saldo = saldo - ? WHERE id = ? AND saldo >= ?',
            (monto, origen, monto)
        )
        if cursor.rowcount != 1:
            raise ValueError('Cuenta origen inexistente o saldo insuficiente')
        # Para el laboratorio: cambiar a True desde el llamado a transferir().
        if simular_error:
            raise RuntimeError('Error simulado en transferencia')
        cursor = conexion.execute('UPDATE cuentas SET saldo = saldo + ? WHERE id = ?', (monto, destino))
        if cursor.rowcount != 1:
            raise ValueError('No se pudo acreditar el dinero')
        conexion.commit()
        print('Transferencia realizada correctamente')
    except (ValueError, RuntimeError, sqlite3.Error) as error:
        conexion.rollback()
        print('Transferencia cancelada:', error)
    finally:
        conexion.close()


def menu():
    while True:
        print('\n===== SISTEMA BANCARIO =====')
        print('1. Crear cuenta')
        print('2. Ver todas las cuentas')
        print('3. Buscar cuenta por ID')
        print('4. Actualizar titular')
        print('5. Eliminar cuenta')
        print('6. Consignar dinero')
        print('7. Retirar dinero')
        print('8. Transferir dinero')
        print('9. Salir')
        opcion = input('Seleccione una opcion: ').strip()
        if opcion == '1': crear_cuenta()
        elif opcion == '2': mostrar_cuentas()
        elif opcion == '3': buscar_cuenta()
        elif opcion == '4': actualizar_titular()
        elif opcion == '5': eliminar_cuenta()
        elif opcion == '6': consignar()
        elif opcion == '7': retirar()
        elif opcion == '8': transferir()
        elif opcion == '9':
            print('Saliendo del sistema...')
            break
        else:
            print('Opcion no valida')


if __name__ == '__main__':
    crear_bd()
    menu()
