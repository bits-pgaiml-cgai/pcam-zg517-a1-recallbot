# Book appointment — procedural steps v1

1. Detect booking intent.
2. Fill slots: name, specialty, day, time (or time_preference), location (LOC-*).
3. Ask clarification for any missing slot (one question at a time).
4. Build pending_booking and present a confirmation summary.
5. On explicit yes, call book_slot (database write).
6. On no, clear awaiting_confirm and ask how to change the booking.
7. Log the booking as an episodic memory event.
