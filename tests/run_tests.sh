#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."

BIN=./vmsim
passed=0
failed=0

check() {
    local name="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        printf '  [OK]   %s\n' "$name"
        passed=$((passed + 1))
    else
        printf '  [FAIL] %s\n         esperado: %s\n         obtenido: %s\n' "$name" "$expected" "$actual"
        failed=$((failed + 1))
    fi
}

field() {
    "$BIN" -c "$@" | tail -n +2 | cut -d, -f1,4,5,7 | tr '\n' ' ' | sed 's/ $//'
}

echo "== Ejemplo del enunciado"
check "basico FIFO (accesos,fallos,reemplazos)" "FIFO,4,2,0" "$(field -p fifo tests/basico.txt)"
check "basico lecturas devuelven lo escrito" "valor=42 valor=99" "$("$BIN" -v tests/basico.txt | grep -o 'valor=[0-9]*' | tr '\n' ' ' | sed 's/ $//')"

echo "== Anomalía de Belady (páginas de 128K)"
check "3 marcos" "FIFO,12,9,6 LRU,12,10,7 CLOCK,12,9,6" "$(field -p all -s 128K -m 384K tests/belady.txt)"
check "4 marcos" "FIFO,12,10,6 LRU,12,8,4 CLOCK,12,10,6" "$(field -p all -s 128K -m 512K tests/belady.txt)"

echo "== Liberación, reutilización y errores"
out="$("$BIN" -v tests/liberacion.txt)"
check "segfaults detectados" "2" "$(grep -c SEGFAULT <<<"$out")"
check "free inválidos" "2" "$(grep -c 'no es el inicio' <<<"$out")"
check "errores de sintaxis" "2" "$(grep -c 'error de sintaxis' <<<"$out")"
check "región reutilizada se entrega en cero" "valor=0" "$(sed -n 's/.*L  13.*\(valor=[0-9]*\).*/\1/p' <<<"$out")"
check "región no liberada conserva datos" "valor=33" "$(sed -n 's/.*L  16.*\(valor=[0-9]*\).*/\1/p' <<<"$out")"

echo "== Persistencia de datos a través de swap"
for policy in fifo lru clock; do
    values="$("$BIN" -v -p "$policy" tests/swap.txt | grep 'read ' | grep -o 'valor=[0-9]*' | cut -d= -f2 | tr '\n' ' ' | sed 's/ $//')"
    check "swap $policy" "10 20 30 40 50 60 70 80 90 100 150 199" "$values"
done

echo "== Validación contra simulador de referencia (Python)"
if command -v python3 >/dev/null 2>&1; then
    for trace in secuencial aleatorio localidad matrices; do
        for frames in 64 128 256; do
            expected="$(python3 tests/referencia.py "tests/$trace.txt" 4096 "$frames" | tr '\n' ' ' | sed 's/ $//')"
            actual="$("$BIN" -c -p all -m "$((frames * 4))K" "tests/$trace.txt" | tail -n +2 | cut -d, -f1,5 | tr '\n' ' ' | sed 's/ $//')"
            check "$trace con $frames marcos" "$expected" "$actual"
        done
    done
else
    echo "  (python3 no disponible, se omite)"
fi

echo "== Configuración inválida"
"$BIN" -m 128K tests/basico.txt >/dev/null 2>&1
check "memoria menor a 256K rechazada" "2" "$?"
"$BIN" -s 3000 tests/basico.txt >/dev/null 2>&1
check "página no potencia de 2 rechazada" "2" "$?"
"$BIN" -m 257K tests/basico.txt >/dev/null 2>&1
check "memoria no múltiplo de página rechazada" "2" "$?"
"$BIN" tests/no_existe.txt >/dev/null 2>&1
check "archivo inexistente" "1" "$?"

echo "== Traducción VA -> PA y tamaño de página configurable"
out="$("$BIN" -v tests/traduccion.txt)"
check "0x00403ABC con páginas de 4K" "(pt1=   1, pt2=   3, off=0xABC) -> PA 0x00000ABC" "$(grep -o '(pt1=.*PA 0x[0-9A-F]*' <<<"$out" | sed -n 1p)"
check "0x007FFFFF con páginas de 4K" "(pt1=   1, pt2=1023, off=0xFFF) -> PA 0x00001FFF" "$(grep -o '(pt1=.*PA 0x[0-9A-F]*' <<<"$out" | sed -n 3p)"
check "tablas de nivel 2 creadas bajo demanda" "Tablas de nivel 2 creadas: 1 (vivas 1)" "$(grep 'Tablas de nivel 2' <<<"$out")"
out="$("$BIN" -v -s 16K tests/traduccion.txt)"
check "0x00403ABC con páginas de 16K (9/9/14)" "(pt1=   0, pt2= 256, off=0x3ABC) -> PA 0x00003ABC" "$(grep -o '(pt1=.*PA 0x[0-9A-F]*' <<<"$out" | sed -n 1p)"
check "basico con páginas de 16K comparte página" "FIFO,4,1,0" "$(field -s 16K -m 256K tests/basico.txt)"

echo
echo "Resultado: $passed pasaron, $failed fallaron"
[[ $failed -eq 0 ]]
