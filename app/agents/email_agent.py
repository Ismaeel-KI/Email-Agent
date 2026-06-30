import logging
from typing import cast
from app.schemas import EmailState, EmailInput
from app.graphs import email_graph

logger = logging.getLogger("email-agent.agent")


class EmailAgent:
    """
    Orchestrates the LangGraph pipeline over a batch of emails.
    Runs each email independently through the graph and collects results.
    """

    def __init__(self) -> None:
        self.graph = email_graph
        logger.info("EmailAgent initialized.")

    def run(self, emails: list[EmailInput]) -> list[EmailState]:
        """
        Process a list of emails through the pipeline.

        Args:
            emails: List of raw EmailInput dicts from GmailClient.

        Returns:
            List of enriched EmailState dicts with category, summary, action.
        """
        if not emails:
            logger.info("No emails to process.")
            return []

        logger.info("Processing %d email(s) through the pipeline...", len(emails))
        results: list[EmailState] = []

        for i, email in enumerate(emails, 1):
            logger.info(
                "[%d/%d] Processing: %s",
                i, len(emails), email["subject"]
            )
            try:
                # Build initial state from raw email
                initial_state: EmailState = {
                    **email,
                    "category": None,
                    "confidence": None,
                    "reasoning": None,
                    "summary": None,
                    "requires_action": None,
                    "action_type": None,
                    "action_detail": None,
                    "deadline": None,
                    "error": None,
                    "skipped": False,
                }

                result = self.graph.invoke(initial_state)
                results.append(cast(EmailState, result))  # ← cast here

            except Exception as e:
                logger.error(
                    "Pipeline failed for '%s': %s",
                    email["subject"], e
                )
                # Append partial result so the digest still shows the email
                results.append({
                    **email,
                    "category": "other",
                    "confidence": 0.0,
                    "reasoning": "",
                    "summary": email.get("snippet", ""),
                    "requires_action": False,
                    "action_type": "none",
                    "action_detail": "",
                    "deadline": None,
                    "error": str(e),
                    "skipped": False,
                })

        logger.info(
            "Pipeline complete. %d/%d emails processed successfully.",
            sum(1 for r in results if not r.get("error")),
            len(emails),
        )
        return results