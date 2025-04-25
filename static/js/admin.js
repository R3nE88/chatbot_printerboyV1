document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("usuarios-container");

    if (!container) return;

    // Cargar usuarios inicialmente
    fetchUsuarios();

    // Consultar los usuarios cada 10 segundos
    setInterval(fetchUsuarios, 10000);
});

function fetchUsuarios() {
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
