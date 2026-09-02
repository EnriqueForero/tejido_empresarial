# Guía sencilla · Poner el aplicativo a funcionar en Railway

Escrita para hacerse paso a paso, sin conocimientos de despliegue. Su dirección
pública es:

**https://tejidoempresarialreact-production.up.railway.app**

Cada vez que esta guía diga «abra el aplicativo», use ese enlace.

---

## Paso 1 · Ver si está conectado (10 segundos)

Abra:

**https://tejidoempresarialreact-production.up.railway.app/estado**

Esa página se llama **Estado del aplicativo** y responde en una frase si está
usando datos reales o de ejemplo. También la alcanza desde el menú superior: la
pastilla de color que está junto al botón «Buscar empresas», o el enlace
«Estado del aplicativo» al final de cualquier página.

Verá uno de estos cuatro estados:

| Lo que ve | Qué significa | Vaya al |
|---|---|---|
| 🟢 **Datos reales** | El aplicativo está conectado a Snowflake. | Paso 5 (verificación final) |
| 🔵 **Modo demostración** | Está mostrando 14 empresas de ejemplo, no reales. | Paso 2 |
| 🟠 **Conexión con problemas** | La configuración está completa, pero la consulta falló. | Paso 4 |
| 🔴 **Sin conexión a datos** | Falta configuración en el servidor. | Paso 3 |

La misma página trae, más abajo, un recuadro **«Detalle del servicio»** con la
versión, si el conector está instalado, cuál llave está configurada y qué
variables faltan. No hace falta que entienda cada campo: los pasos siguientes le
dicen qué hacer con esa información.

---

## Paso 2 · Si dice «Modo demostración»

Significa que en Railway quedó activada la variable `APP_DEMO_MODE`.

1. Entre a [railway.app](https://railway.app) y abra su proyecto.
2. Haga clic en el servicio del aplicativo.
3. Pestaña **Variables**.
4. Busque `APP_DEMO_MODE` y **bórrela** (o cámbiela a `false`).
5. Railway vuelve a desplegar solo. Espere 2 o 3 minutos.
6. Recargue la página de estado.

---

## Paso 3 · Si dice «Sin conexión a datos»

Falta al menos una variable. La página de estado, en «Detalle del servicio» →
**Variables faltantes**, le dice exactamente cuáles, en rojo.

En Railway → su servicio → **Variables**, agregue las que falten:

| Variable | Qué poner |
|---|---|
| `SF_ACCOUNT` | La cuenta de Snowflake, la misma de la versión anterior (por ejemplo `my17686.us-east-2.aws`) |
| `SF_USER` | El usuario de servicio |
| `SF_DATABASE` | `APP_SEGMENTACION_EXPORTACIONES` |
| `SF_SCHEMA` | `SEGMENTACION` |
| `SF_WAREHOUSE` | `APPS_WH` |
| `SF_ROLE` | `APP_SEGMENTACION_EXPORTACIONES` |
| `SF_PRIVATE_KEY_B64_1` | La llave `rsa_key_1.der` convertida a texto (ver abajo) |
| `SF_PRIVATE_KEY_PASSPHRASE_1` | Sólo si la llave tiene contraseña |

**Cómo convertir la llave a texto.** En su computador, abra PowerShell en la
carpeta donde está el archivo `.der` y ejecute:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("rsa_key_1.der")) | Set-Clipboard
```

Eso deja el valor copiado. Péguelo en Railway **en una sola línea**, sin comillas.
Si el resultado ocupa varias líneas al pegarlo, no pasa nada: desde la versión
3.3.0 el aplicativo tolera espacios y saltos de línea.

Guarde, espere el redespliegue y recargue la página de estado.

---

## Paso 4 · Si dice «Conexión con problemas» (o las búsquedas fallan)

La página de estado tiene un botón **«Ver diagnóstico detallado»**. Ese
diagnóstico revisa la cadena completa y marca con ✓ o ✗ cada eslabón:

```
✓ Variables de Snowflake presentes
✓ Conector snowflake-snowpark-python disponible
✓ Llave privada 1 interpretable
✗ Sesión establecida con Snowflake   ← aquí está el problema
```

Debajo del primer ✗ aparece el mensaje real de Snowflake y un recuadro
**«Qué hacer»** con la corrección concreta.

### Para poder abrir el diagnóstico

Como el diagnóstico muestra detalles del servidor, sólo funciona si el
despliegue está protegido. Elija **una** de las dos opciones, en Railway →
Variables:

**Opción A (recomendada).** Protege además todo el aplicativo con contraseña,
que es lo aconsejable porque las descargas incluyen datos de contacto de
empresas reales:

```
APP_BASIC_USER      = procolombia
APP_BASIC_PASSWORD  = (una contraseña larga que usted elija)
```

Al entrar, el navegador le pedirá ese usuario y contraseña una sola vez.

**Opción B (sólo para revisar ahora).**

```
APP_DIAG_TOKEN = (una palabra larga cualquiera, por ejemplo revision-2026-tejido)
```

Y luego abra directamente, con su palabra al final:

`https://tejidoempresarialreact-production.up.railway.app/estado?token=revision-2026-tejido`

Con ese enlace el diagnóstico se ejecuta solo.

### Qué significa cada ✗

| Paso en rojo | Qué corregir |
|---|---|
| **Variables de Snowflake presentes** | Falta una variable: la lista aparece en el mensaje. Vuelva al paso 3. |
| **Conector … disponible** | La imagen se construyó mal. En Railway, pestaña Deployments → vuelva a desplegar el último commit. |
| **Llave privada 1 interpretable** | El valor pegado no corresponde al archivo `.der`, está incompleto, o la contraseña de la llave no es la correcta. Repita la conversión del paso 3. |
| **Sesión establecida con Snowflake** | Snowflake rechazó la conexión. Tres causas típicas, y el mensaje de error dice cuál: la llave pública no está registrada en el usuario de servicio (se corrige en Snowflake con `ALTER USER … SET RSA_PUBLIC_KEY=…`); el rol o el warehouse no existen o el usuario no los tiene asignados; o una política de red de Snowflake bloquea la dirección IP de Railway (el mensaje dice «not allowed to access»). Este último punto lo resuelve el administrador de Snowflake. |
| **Filtros generales / Filtros de exportaciones / Tabla de empresas / Tabla de bienes** | El rol de Snowflake no tiene permiso de lectura sobre esa tabla. El administrador debe ejecutar `GRANT SELECT ON <la tabla que aparece> TO ROLE APP_SEGMENTACION_EXPORTACIONES;` |
| **Tabla de auditoría de eventos** | Sólo afecta el registro de uso. El aplicativo funciona igual. |

Después de cada corrección: espere el redespliegue de Railway y pulse
**«Probar la conexión ahora»** en la página de estado.

---

## Paso 5 · Verificación final (2 minutos)

1. La página de estado muestra 🟢 **Datos reales**.
2. Pulse **«Probar la conexión ahora»**: debe responder «La conexión funciona».
3. Vaya a **Consultar** → *Segmentar con filtros*: el panel debe traer
   departamentos, tamaños y cadenas reales.
4. Elija un departamento y confirme que la lista de municipios se reduce sola.
5. Pulse **Buscar empresas**: deben aparecer resultados con el conteo real.
6. Abra la ficha de una empresa desde la tabla.
7. Descargue el Excel y ábralo.
8. Abra el mismo enlace en su celular.

---

## Si prefiere revisar sin abrir el aplicativo

Estas direcciones devuelven texto técnico; sirven para enviarle el resultado a
alguien de sistemas:

- Estado rápido, no pide contraseña:
  `https://tejidoempresarialreact-production.up.railway.app/api/health`
- Prueba real contra Snowflake:
  `https://tejidoempresarialreact-production.up.railway.app/api/health?deep=true`
- Diagnóstico completo (requiere la protección del paso 4):
  `https://tejidoempresarialreact-production.up.railway.app/api/diagnostico`

También puede ver los registros del servicio en Railway: su proyecto → el
servicio → pestaña **Deployments** → **View Logs**. Busque las líneas que
empiezan con `La consulta falló` o `Diagnóstico: falló el paso`.

---

## Recordatorio de seguridad

Mientras `APP_BASIC_USER` y `APP_BASIC_PASSWORD` estén vacías, cualquiera con el
enlace entra al aplicativo y puede descargar datos de contacto de empresas
reales. La propia página de estado se lo advierte en amarillo. Configurarlas es
un minuto y no cambia nada más del funcionamiento.
