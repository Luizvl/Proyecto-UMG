/* Detalles visuales del panel de administración — Byron.
   Solo cambia cómo se ven algunas celdas; no envía ni modifica datos. */
(function () {
    "use strict";

    function clave(texto) {
        return texto.trim().toLowerCase()
            .normalize("NFD").replace(/[̀-ͯ]/g, "")
            .replace(/\s+/g, "_");
    }

    // Estados y roles como etiquetas de colores
    var columnas = ["estado", "rol", "tipo_beca", "nivel_academico", "accion"];
    columnas.forEach(function (campo) {
        document.querySelectorAll("#result_list td.field-" + campo).forEach(function (td) {
            var texto = td.textContent.trim();
            if (!texto || texto === "-") return;
            var span = document.createElement("span");
            span.className = "pn-badge pn-badge-" + clave(texto);
            span.textContent = texto;
            td.textContent = "";
            td.appendChild(span);
        });
    });

    // Buscador con texto de ayuda
    var buscador = document.getElementById("searchbar");
    if (buscador && !buscador.placeholder) {
        var titulo = document.querySelector(".titles h1");
        buscador.placeholder = "Buscar " + (titulo ? titulo.textContent.trim().toLowerCase() : "") + "…";
    }

    // Cierra el menú del usuario al hacer clic fuera
    document.addEventListener("click", function (e) {
        document.querySelectorAll("details.pn-usuario[open]").forEach(function (d) {
            if (!d.contains(e.target)) d.removeAttribute("open");
        });
    });
})();

/* Textos de la barra de acciones que Django todavía muestra en inglés */
(function () {
    var barra = document.querySelector("#changelist .actions");
    if (!barra) return;
    var boton = barra.querySelector("button[type=submit], input[type=submit]");
    if (boton && /^run$/i.test((boton.textContent || boton.value).trim())) {
        if (boton.tagName === "INPUT") boton.value = "Aplicar"; else boton.textContent = "Aplicar";
    }
    var vacia = barra.querySelector("select option[value='']");
    if (vacia && /select an option/i.test(vacia.textContent)) vacia.textContent = "— Elige una acción —";
})();
