// Handle Add XP form
document.getElementById("xp-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    const amount = document.getElementById("xp-amount").value;
    const skill = document.getElementById("skill-select").value;

    const response = await fetch("/add_xp", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ skill: skill, xp: amount })
    });

    if (response.ok) {
        const data = await response.json();
        const newLevel = data.current_level;
        const previousLevel = data.old_level;

        if (newLevel > previousLevel) {
            const skillElements = document.querySelectorAll(".skill-bar .skill-name");

            skillElements.forEach(el => {
                if (el.textContent.includes(skill)) {
                    const skillBar = el.closest(".skill-bar");
                    skillBar.classList.add("level-up");

                    // Remove class after animation so it can be retriggered
                    skillBar.addEventListener("animationend", () => {
                        skillBar.classList.remove("level-up");
                    }, { once: true });
                }
            });

            setTimeout(() => location.reload(), 600);
        } else {
            location.reload();
        }
    } else {
        alert("Failed to add XP");
    }
});

// Handle Delete XP form
document.getElementById("xp-delete-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    const amount = document.getElementById("xp-delete-amount").value;
    const skill = document.getElementById("skill-delete-select").value;

    const response = await fetch("/delete_xp", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ skill: skill, xp: amount })
    });

    if (response.ok) {
        location.reload();
    } else {
        alert("Failed to delete XP");
    }
});

// Handle inline Add XP buttons
document.querySelectorAll(".xp-add-btn-inline").forEach(btn => {
    btn.addEventListener("click", async () => {
        const skill = btn.dataset.skill;
        const category = btn.dataset.category;
        const amount = parseInt(btn.dataset.add, 10);

        const response = await fetch("/add_xp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skill: skill, xp: amount, category: category })
        });

        if (response.ok) {
            const data = await response.json();
            const newLevel = data.current_level;
            const previousLevel = data.old_level;

            if (newLevel > previousLevel) {
                const skillElements = document.querySelectorAll(".skill-bar .skill-name");
                skillElements.forEach(el => {
                    if (el.textContent.includes(skill)) {
                        const skillBar = el.closest(".skill-bar");
                        skillBar.classList.add("level-up");
                        skillBar.addEventListener("animationend", () => {
                            skillBar.classList.remove("level-up");
                        }, { once: true });
                    }
                });
                setTimeout(() => location.reload(), 600);
            } else {
                location.reload();
            }
        } else {
            alert("Failed to add XP");
        }
    });
});

// Handle inline Delete XP buttons
document.querySelectorAll(".xp-del-btn-inline").forEach(btn => {
    btn.addEventListener("click", async () => {
        const skill = btn.dataset.skill;
        const category = btn.dataset.category;
        const amount = parseInt(btn.dataset.add, 10);

        const response = await fetch("/delete_xp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skill: skill, xp: amount, category: category })
        });

        if (response.ok) {
            location.reload();
        } else {
            alert("Failed to delete XP");
        }
    });
});


// Toggle category details
function toggleDetails(category) {
    const section = document.getElementById(`details-${category}`);
    const arrow = section.previousElementSibling.querySelector(".arrow");

    if (section.style.display === "block") {
        section.style.display = "none";
        arrow.style.transform = "rotate(0deg)";
    } else {
        section.style.display = "block";
        arrow.style.transform = "rotate(90deg)";
    }
}

// Toggle skill details
function toggleSkillDetails(skillId) {
    const section = document.getElementById(`details-${skillId}`);
    const arrow = section.previousElementSibling.querySelector(".arrow");
    const isVisible = section.style.display === "block";

    section.style.display = isVisible ? "none" : "block";
    arrow.textContent = isVisible ? "▶" : "▼";
}

// Quick-add buttons for Add XP form
document.querySelectorAll(".xp-add-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const input = document.getElementById("xp-amount");
        const addValue = parseInt(btn.dataset.add, 10);
        input.value = (parseInt(input.value || "0", 10) + addValue);
    });
});

// Quick-del buttons for Delete XP form
document.querySelectorAll(".xp-del-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const input = document.getElementById("xp-delete-amount");
        const delValue = parseInt(btn.dataset.add, 10);
        input.value = (parseInt(input.value || "0", 10) + delValue);
    });
});
