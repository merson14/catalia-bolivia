const COUNTRIES = [
    { iso: "BO", name: "Bolivia", dial: "591", c1: "#d52b1e", c2: "#f9e300", c3: "#007934" },
    { iso: "PE", name: "Perú", dial: "51", c1: "#d91023", c2: "#ffffff", c3: "#d91023" },
    { iso: "CL", name: "Chile", dial: "56", c1: "#0039a6", c2: "#ffffff", c3: "#d52b1e" },
    { iso: "AR", name: "Argentina", dial: "54", c1: "#74acdf", c2: "#ffffff", c3: "#74acdf" },
    { iso: "CO", name: "Colombia", dial: "57", c1: "#fcd116", c2: "#003893", c3: "#ce1126" },
    { iso: "MX", name: "México", dial: "52", c1: "#006847", c2: "#ffffff", c3: "#ce1126" },
    { iso: "EC", name: "Ecuador", dial: "593", c1: "#ffd100", c2: "#034ea2", c3: "#ed1c24" },
    { iso: "PY", name: "Paraguay", dial: "595", c1: "#d52b1e", c2: "#ffffff", c3: "#0038a8" },
    { iso: "UY", name: "Uruguay", dial: "598", c1: "#0038a8", c2: "#ffffff", c3: "#0038a8" },
    { iso: "BR", name: "Brasil", dial: "55", c1: "#009c3b", c2: "#ffdf00", c3: "#002776" },
    { iso: "VE", name: "Venezuela", dial: "58", c1: "#ffcc00", c2: "#00247d", c3: "#cf142b" },
    { iso: "ES", name: "España", dial: "34", c1: "#aa151b", c2: "#f1bf00", c3: "#aa151b" },
    { iso: "US", name: "Estados Unidos", dial: "1", c1: "#3c3b6e", c2: "#ffffff", c3: "#b22234" }
];

function buildFlagSvg(country) {
    return `
        <svg viewBox="0 0 24 16" class="w-full h-full" aria-label="${country.name}">
            <rect x="0" y="0" width="24" height="5.33" fill="${country.c1}" />
            <rect x="0" y="5.33" width="24" height="5.33" fill="${country.c2}" />
            <rect x="0" y="10.66" width="24" height="5.34" fill="${country.c3}" />
        </svg>
    `;
}

function populateCountrySelect(selectId = "reg-country-code", flagContainerId = "country-flag-icon") {
    const select = document.getElementById(selectId);
    if (!select) return;

    select.innerHTML = COUNTRIES.map((country, index) => {
        const selectedAttr = index === 0 ? "selected" : "";
        return `<option value="${country.dial}" data-iso="${country.iso}" ${selectedAttr}>+${country.dial} (${country.iso})</option>`;
    }).join("");

    updateCountryFlag(selectId, flagContainerId);
}

function updateCountryFlag(selectId = "reg-country-code", flagContainerId = "country-flag-icon") {
    const select = document.getElementById(selectId);
    const iconBox = document.getElementById(flagContainerId);
    if (!select || !iconBox) return;

    const selectedOption = select.options[select.selectedIndex];
    const iso = selectedOption?.getAttribute("data-iso") || "BO";
    const country = COUNTRIES.find((item) => item.iso === iso) || COUNTRIES[0];
    iconBox.innerHTML = buildFlagSvg(country);
}