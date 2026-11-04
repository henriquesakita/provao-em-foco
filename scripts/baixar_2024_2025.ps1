$ErrorActionPreference = "Stop"
$base2024 = "https://vncdndev.azureedge.net/lib/SEED2405"
$base2025 = "https://stcdndev.blob.core.windows.net/lib/SEED2503/ProvasGabaritos"
$root = "C:\Users\Sakita\Documents\GitHub\provao-paulista\data\raw"

$arquivos = @(
    @{ ano = 2024; nome = "2024-1a-lc-cn.pdf"; url = "$base2024/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_101_LT-CNT-1%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2024; nome = "2024-1a-mt-ch.pdf"; url = "$base2024/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_151_MT-CHSA-1%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2024; nome = "2024-2a-lc-cn.pdf"; url = "$base2024/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_201_LT-CNT-2%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2024; nome = "2024-2a-mt-ch.pdf"; url = "$base2024/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_251_MT-CHSA-2%C2%AASerieEM_016_1.pdf" },
    @{ ano = 2024; nome = "2024-3a-lc-cn.pdf"; url = "$base2024/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_301_LT-CNT-RD-3%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2024; nome = "2024-3a-mt-ch.pdf"; url = "$base2024/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_351_MT-CHSA-3%C2%AASerieEM_016_1.pdf" },
    @{ ano = 2024; nome = "2024-1a-gab-d1.pdf"; url = "$base2024/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_101_Gabarito_1.pdf" },
    @{ ano = 2024; nome = "2024-1a-gab-d2.pdf"; url = "$base2024/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_151_Gabarito_1.pdf" },
    @{ ano = 2024; nome = "2024-2a-gab-d1.pdf"; url = "$base2024/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_201_Gabarito_1.pdf" },
    @{ ano = 2024; nome = "2024-2a-gab-d2.pdf"; url = "$base2024/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_251_Gabarito_1.pdf" },
    @{ ano = 2024; nome = "2024-3a-gab-d1.pdf"; url = "$base2024/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_301_Gabarito_1.pdf" },
    @{ ano = 2024; nome = "2024-3a-gab-d2.pdf"; url = "$base2024/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_351_Gabarito_1.pdf" },
    @{ ano = 2025; nome = "2025-1a-lc-cn.pdf"; url = "$base2025/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_101_LT-CNT-1%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2025; nome = "2025-1a-mt-ch.pdf"; url = "$base2025/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_151_MT-CHSA-1%C2%AASerieEM_020_1.pdf" },
    @{ ano = 2025; nome = "2025-2a-lc-cn.pdf"; url = "$base2025/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_201_LT-CNT-2%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2025; nome = "2025-2a-mt-ch.pdf"; url = "$base2025/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_251_MT-CHSA-2%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2025; nome = "2025-3a-lc-cn.pdf"; url = "$base2025/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_301_LT-CNT-RD-3%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2025; nome = "2025-3a-mt-ch.pdf"; url = "$base2025/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_351_MT-CHSA-3%C2%AASerieEM_024_1.pdf" },
    @{ ano = 2025; nome = "2025-1a-gab-d1.pdf"; url = "$base2025/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_101_Gabarito_1.pdf" },
    @{ ano = 2025; nome = "2025-1a-gab-d2.pdf"; url = "$base2025/1%C2%BA%20Ano%20EM%20-%20Prova%20Principal_151_Gabarito_1.pdf" },
    @{ ano = 2025; nome = "2025-2a-gab-d1.pdf"; url = "$base2025/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_201_Gabarito_1.pdf" },
    @{ ano = 2025; nome = "2025-2a-gab-d2.pdf"; url = "$base2025/2%C2%BA%20Ano%20EM%20-%20Prova%20Principal_251_Gabarito_1.pdf" },
    @{ ano = 2025; nome = "2025-3a-gab-d1.pdf"; url = "$base2025/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_301_Gabarito_1.pdf" },
    @{ ano = 2025; nome = "2025-3a-gab-d2.pdf"; url = "$base2025/3%C2%BA%20Ano%20EM%20-%20Prova%20Principal_351_Gabarito_1.pdf" }
)

foreach ($a in $arquivos) {
    $destino = Join-Path (Join-Path $root $a.ano) $a.nome
    curl.exe -L -s -f -o $destino $a.url
    if (-not (Test-Path $destino)) { throw "Falhou: $($a.nome)" }
    $tam = (Get-Item $destino).Length
    Write-Output "$($a.ano)/$($a.nome) $tam"
}
Remove-Item "$root\teste.pdf","$root\teste2.pdf","$root\teste3.pdf","$root\page.html","C:\Users\Sakita\Documents\GitHub\provao-paulista\cookies.txt" -ErrorAction SilentlyContinue
