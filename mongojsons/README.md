# MongoDB JSON Seed Files

Este directorio contiene archivos JSON con datos de ejemplo para inicializar la base de datos MongoDB.

## Archivos incluidos:

- `categories.json`: Categorías de ingresos y gastos
- `users.json`: Usuarios de ejemplo con diferentes roles (password: "password" para todos)
  - Basic: demo@moneyapp.com (10 requests AI/mes)
  - Pro: juan@example.com (100 requests AI/mes)  
  - Max: admin@moneyapp.com (requests AI ilimitados)
- `accounts.json`: Cuentas de ejemplo vinculadas a usuarios
- `transactions.json`: Transacciones de ejemplo
- `budgets.json`: Presupuestos de ejemplo

## Instrucciones de uso:

1. Asegúrate de que MongoDB esté ejecutándose en `localhost:27017`
2. Crea la base de datos `moneyapp`
3. Importa cada colección usando mongoimport:

```bash
# Importar categorías
mongoimport --db moneyapp --collection categories --file categories.json --jsonArray

# Importar usuarios
mongoimport --db moneyapp --collection users --file users.json --jsonArray

# Importar cuentas (reemplaza los REPLACE_WITH_USER_ID con IDs reales)
mongoimport --db moneyapp --collection accounts --file accounts.json --jsonArray

# Importar transacciones (reemplaza los IDs con valores reales)
mongoimport --db moneyapp --collection transactions --file transactions.json --jsonArray

# Importar presupuestos (reemplaza los IDs con valores reales)
mongoimport --db moneyapp --collection budgets --file budgets.json --jsonArray
```

## Notas importantes:

- Los archivos con `REPLACE_WITH_*_ID` necesitan que reemplaces esos placeholders con ObjectIds reales de MongoDB
- Todos los usuarios de ejemplo tienen la contraseña "password" (hash SHA256)
- Los timestamps están en formato ISO 8601 UTC
- Las cuentas incluyen ejemplos en USD y CUP
- Los presupuestos tienen estados de completado y pendiente

## Estructura de la base de datos:

- **users**: Información de usuarios con autenticación
- **accounts**: Cuentas financieras (billetera, tarjeta, ahorro)
- **transactions**: Historial de ingresos, gastos y transferencias
- **categories**: Categorías predefinidas para clasificar transacciones
- **budgets**: Metas de ahorro con seguimiento de progreso