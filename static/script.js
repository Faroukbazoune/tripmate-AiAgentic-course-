async function planTrip() {

    const queryInput =
        document.getElementById("userQuery");

    const button =
        document.getElementById("submitButton");

    const loading =
        document.getElementById("loading");

    const results =
        document.getElementById("results");

    const errorBox =
        document.getElementById("error");


    const query =
        queryInput.value.trim();


    if (!query) {

        alert("Please enter your travel request.");

        return;
    }


    button.disabled = true;

    button.innerText = "Planning...";

    loading.style.display = "block";

    results.style.display = "none";

    errorBox.style.display = "none";


    try {

        const response = await fetch(
            "/api/travel",
            {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    // IMPORTANT:
                    // Your Pydantic model calls this "message"

                    message: query,

                    thread_id: null

                })

            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                `Server error: ${response.status}`
            );
        }


        // =========================
        // Final answer
        // =========================

        document.getElementById(
            "finalAnswer"
        ).innerText =
            data.answer ||
            "No answer returned.";


        // =========================
        // Flights
        // =========================

        document.getElementById(
            "flightResults"
        ).innerText =
            data.flight_agent_response ||
            "No flight information available.";


        // =========================
        // Hotels
        // =========================

        document.getElementById(
            "hotelResults"
        ).innerText =
            data.hotel_agent_response ||
            "No hotel information available.";


        // =========================
        // Itinerary
        // =========================

        document.getElementById(
            "itineraryResults"
        ).innerText =
            data.itinerary_agent_response ||
            "No itinerary generated.";


        // =========================
        // Thread ID
        // =========================

        document.getElementById(
            "threadId"
        ).innerText =
            "Conversation ID: " +
            data.thread_id;


        // Show results

        results.style.display = "block";

    }


    catch (error) {

        console.error(error);

        errorBox.innerText =
            "Something went wrong: " +
            error.message;

        errorBox.style.display = "block";

    }


    finally {

        loading.style.display = "none";

        button.disabled = false;

        button.innerText = "Plan My Trip";

    }

}