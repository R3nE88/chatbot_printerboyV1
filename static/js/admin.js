document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("usuarios-container");
    

    if (!container) return;

    // Cargar usuarios inicialmente
    fetchUsuarios();

    // Consultar los usuarios cada 30 segundos
    setInterval(fetchUsuarios, 30000);
});

function fetchUsuarios() {
    const botSwitch = document.getElementById("bot-switch");
    const botStatusText = document.getElementById("bot-status-text");

    if (botSwitch && botStatusText) {
        // Cargar estado inicial del bot
        fetch("/api/bot_estado")
            .then(response => response.json())
            .then(data => {
                botSwitch.checked = data.activo;
                botStatusText.textContent = data.activo ? "Bot activo" : "Bot inactivo";
            })
            .catch(err => console.error("Error al cargar estado del bot:", err));

        // Cambiar estado al mover el switch
        botSwitch.addEventListener("change", () => {
            const url = botSwitch.checked ? "/bot/on" : "/bot/off";
            fetch(url, { method: "POST" })
                .then(() => {
                    botStatusText.textContent = botSwitch.checked ? "Bot activo" : "Bot inactivo";
                })
                .catch(err => console.error("Error al cambiar estado global del bot:", err));
        });
    }
    fetch("/api/usuarios")
        .then(response => response.json())
        .then(usuarios => {
            // Limpiar el contenedor antes de agregar los nuevos usuarios
            const container = document.getElementById("usuarios-container");
            container.innerHTML = ""; // Limpiar el contenedor

            // Recorrer los usuarios y crear los elementos HTML
            for (const [id, info] of Object.entries(usuarios)) {
                const userDiv = document.createElement("div");
                userDiv.className = "usuario";

                const nombre = document.createElement("span");
                nombre.textContent = info.nombre || "Desconocido";
                nombre.className = "nombre";

                const idSpan = document.createElement("span");
                idSpan.textContent = `ID: ${id}`;
                idSpan.className = "user-id";

                const label = document.createElement("label");
                label.className = "switch";

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.checked = info.activo;

                checkbox.addEventListener("change", () => {
                    // Enviar la solicitud para cambiar el estado del usuario
                    fetch(`/toggle/${id}`, { method: "POST" })
                        .then(() => {
                            console.log(`Estado de ${info.nombre} actualizado`);
                        })
                        .catch(err => console.error("Error al cambiar estado:", err));
                });

                const slider = document.createElement("span");
                slider.className = "slider";

                label.appendChild(checkbox);
                label.appendChild(slider);

                userDiv.appendChild(nombre);
                userDiv.appendChild(idSpan);
                userDiv.appendChild(label);

                container.appendChild(userDiv);
            }
        })
        .catch(err => console.error("Error al obtener los usuarios:", err));
}
