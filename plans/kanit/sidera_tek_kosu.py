"""Sidera'da tek kosu sinamasi (6 Eki 2026). Sidera ortaminda calistirilir:
    D:\\sidera\\.venv\\Scripts\\python.exe plans/kanit/sidera_tek_kosu.py

Soru 1: Kullanici tanimli (protokol) bir atmosfer sinifi, Sidera'nin suruklenme
        modeli uzerinden yayilimi surebiliyor mu?
Soru 2: 4 saatlik bir kosu ne kadar suruyor?
Soru 3: Sabit yogunlukta %20 fark, iz boyunca (3/2)*a_drag*eps*t^2 ile uyumlu mu?
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
from sidera.common.config_types.type_defs import SpacecraftProps
from sidera.core.body_engine.orbits import propagate_body_orbit
from sidera.core.config import load_body_config
from sidera.core.drag.aerodynamics import AtmosphericDrag, EarthRotationAngleModel
from sidera.frames.geodesy import WGS84
from sidera.frames.local_orbital import to_ric
from sidera.physics.atmosphere.models import AtmosphereSample, AtmosphereState

EPOCH_TDB_S = 1.2e8  # 2003-10-xx civari; sabit yogunlukta onemi yok


@dataclass(frozen=True, slots=True)
class ConstantAtmosphere:
    """Protokolu saglayan en kucuk model: her yerde ayni yogunluk."""

    density_kg_m3: float
    label: str
    ellipsoid: Any = WGS84

    @property
    def name(self) -> str:
        return f"constant-{self.label}"

    def evaluate(self, sample: AtmosphereSample) -> AtmosphereState:
        return AtmosphereState(density_kg_m3=self.density_kg_m3, model=self.name)

    def provenance(self) -> dict[str, Any]:
        return {"model": self.name, "density_kg_m3": self.density_kg_m3}


def run(density: float, label: str, spacecraft: SpacecraftProps, cfg: Any) -> tuple[Any, float]:
    drag = AtmosphericDrag(
        atmosphere=ConstantAtmosphere(density, label),
        spacecraft=spacecraft,
        rotation=EarthRotationAngleModel(),
        epoch_tdb_s_at_t0=EPOCH_TDB_S,
    )
    t0 = time.perf_counter()
    result = propagate_body_orbit(cfg, drag=drag)
    return result, time.perf_counter() - t0


def main() -> None:
    rho0 = 4.0e-12  # kg/m^3, ana plandaki ornek
    eps = 0.20
    cd, mass = 2.2, 522.0
    cd_a_over_m = 0.00477  # CHAMP, Gondelach ve Linares (ana plan)
    area = cd_a_over_m * mass / cd
    spacecraft = SpacecraftProps(mass_kg=mass, area_m2=area, cd=cd, cr=1.0)
    cfg = replace(
        load_body_config(
            "earth",
            periapsis_altitude_m=400_000.0,
            eccentricity=0.0005,
            inclination_deg=87.3,
            duration_s=4.0 * 3600.0,
            output_dt_s=60.0,
        ),
        spacecraft=spacecraft,
    )
    cfg.validate()
    print("Sidera cekim ayari:", getattr(cfg, "gravity", None) or "(varsayilan)")

    ref, t_ref = run(rho0, "ref", spacecraft, cfg)
    pert, t_pert = run(rho0 * (1.0 + eps), "plus20pct", spacecraft, cfg)
    print("kosu suresi: referans %.1f s, +%%20 %.1f s (4 sa yayilim, 60 s cikti)" % (t_ref, t_pert))
    print("rhs yolu:", ref.diagnostics.get("rhs_path"), "| cikti noktasi:", len(ref.t))

    # Iz boyunca fark: referans yorungenin RIC cercevesinde, pozitif = ileride.
    # Daha yogun atmosfer yorungeyi alcaltir, ortalama hareket artar: uydu ILERIYE gider.
    assert np.allclose(ref.t, pert.t)
    dr = pert.y[:, :3] - ref.y[:, :3]
    ric = to_ric(dr, ref.y[:, :3], ref.y[:, 3:6])
    along = ric[:, 1]
    v = np.linalg.norm(ref.y[0, 3:6])
    a_drag = 0.5 * rho0 * v**2 * cd_a_over_m
    print("hiz %.1f m/s, a_drag %.3e m/s^2" % (v, a_drag))
    print("%6s %12s %12s %8s %12s" % ("t [sa]", "olculen [m]", "formul [m]", "oran", "radyal [m]"))
    for hours in (1.0, 2.0, 3.0, 4.0):
        i = int(np.argmin(np.abs(ref.t - hours * 3600.0)))
        formula = 1.5 * a_drag * eps * (ref.t[i]) ** 2
        print(
            "%6.2f %12.2f %12.2f %8.3f %12.3f"
            % (ref.t[i] / 3600.0, along[i], formula, along[i] / formula, ric[i, 0])
        )
    print(
        "Isaret: pozitif = daha yogun atmosferdeki uydu referansin ilerisinde (yorunge alcalir, hizlanir)."
    )


if __name__ == "__main__":
    main()
