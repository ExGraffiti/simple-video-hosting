// Извлечение токена из URL и сохранение в localStorage
const extractTokenFromURL = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("access_token");
    if (token) {
        localStorage.setItem("access_token", token); // Сохраняем токен в localStorage
        window.history.replaceState({}, document.title, "/"); // Убираем токен из URL
    }
};

// Проверка авторизации
const checkAuth = async () => {
    const token = localStorage.getItem("access_token");
    if (token) {
        // Пользователь авторизован
        document.getElementById("loginButton").style.display = "none";
        document.getElementById("logoutButton").style.display = "inline-block";
        document.getElementById("uploadSection").style.display = "block";
        loadVideos(); // Загружаем список видео
    } else {
        // Пользователь не авторизован
        document.getElementById("loginButton").style.display = "inline-block";
        document.getElementById("logoutButton").style.display = "none";
        document.getElementById("uploadSection").style.display = "none";
    }
};

// Авторизация через Google
document.getElementById("loginButton").addEventListener("click", () => {
    window.location.href = "/login";
});

// Выход
document.getElementById("logoutButton").addEventListener("click", () => {
    localStorage.removeItem("access_token"); // Удаляем токен
    window.location.href = "/"; // Перенаправляем на главную страницу
});

// Загрузка списка видео
const loadVideos = async () => {
    try {
        const token = localStorage.getItem("access_token");
        const response = await fetch("/files", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) {
            throw new Error("Ошибка при загрузке списка видео");
        }

        const data = await response.json();
        if (data.Ok) {
            const videoList = document.getElementById("videoList");
            videoList.innerHTML = "";
            data.file_content.forEach(video => {
                const videoItem = document.createElement("div");
                videoItem.className = "video-item";

                const img = document.createElement("img");
                img.src = `/image/${video}`;
                img.alt = video;

                videoItem.addEventListener("click", () => {
                    window.location.href = `/watch/${video}`;
                });

                videoItem.appendChild(img);
                videoList.appendChild(videoItem);
            });
        }
    } catch (error) {
        console.error("Ошибка:", error);
        alert("Ошибка при загрузке списка видео");
    }
};

// Загрузка видео и превью
document.getElementById("uploadButton").addEventListener("click", async () => {
    const video = document.getElementById("videoFile").files[0];
    const preview = document.getElementById("previewFile").files[0];

    if (video && preview) {
        const videoName = video.name.replace(".mp4", "");
        const previewName = preview.name.replace(".png", "");
        if (videoName !== previewName) {
            alert("Названия видео и превью должны совпадать (без расширения).");
            return;
        }

        const formData = new FormData();
        formData.append("video_file", video);
        formData.append("preview_file", preview);

        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch("/file", {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            });

            const data = await response.json();
            if (data.Ok) {
                alert("Файлы успешно загружены!");
                loadVideos(); // Обновляем список видео
            } else {
                alert("Ошибка при загрузке файлов.");
            }
        } catch (error) {
            console.error("Ошибка:", error);
            alert("Ошибка при загрузке файлов.");
        }
    } else {
        alert("Выберите оба файла: видео и превью.");
    }
});

// Извлечение токена из URL и проверка авторизации при загрузке страницы
extractTokenFromURL();
checkAuth();