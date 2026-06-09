# LangChain Multimodal Shopping Agent

A multimodal shopping assistant built with LangChain, Groq-hosted LLMs, SQLite, and Streamlit. The project includes a lightweight Streamlit-based demo UI and supports natural language product search, image-based product discovery, product rating retrieval, and order placement through tool calling.

This project demonstrates how Large Language Models (LLMs) can be integrated with external tools, databases, and multimodal image understanding to build a practical AI-powered shopping experience.

## Overview

The application behaves like a simple shopping assistant. A user can ask for products in natural language, filter by price or organic status, check ratings, upload a product image to find similar items, and confirm an order.

Example queries:

```text
I want organic honey under $20 with 4+ rating
```

```text
Find headphones under $100 with good ratings
```

```text
Order the first one
```

The agent uses tools to interact with the database instead of answering only from the model's internal knowledge.

## Key Features

- Product search using natural language queries
- Price and organic product filtering
- Product rating lookup from review data
- Simulated checkout and order creation
- Image-based product search using a multimodal LLM
- Streamlit chat UI with session-based conversation history
- SQLite database with products, reviews, and orders
- Guardrails for shopping-only interactions
- Multilingual query support powered by the underlying LLM

## Tech Stack

- Python
- LangChain
- Groq LLM API
- Streamlit
- SQLite
- Multimodal LLM for image understanding

## Architecture

```text
User
  ↓
Streamlit UI
  ↓
LangChain Agent
  ↓
Tools
  ├─ search_products
  ├─ get_rating
  ├─ checkout
  └─ describe_product_image
  ↓
SQLite Database / Vision LLM
```

The project separates the UI, agent orchestration, and database logic.

```text
app.py
  Streamlit UI, chat history, image upload flow

shopping_agent.py
  LangChain agent, tool definitions, system prompt, LLM configuration

db_service.py
  SQLite database access layer for products, reviews, and orders

store.db
  SQLite database file
```

## Database Design

The project uses SQLite as a lightweight local database.

Main tables:

```text
products
- id
- name
- category
- brand
- price
- stock_quantity
- rating
- review_count
- is_organic
- description
```

```text
reviews
- id
- product_id
- rating
- reviewer_name
- review_text
- review_date
```

```text
orders
- id
- product_id
- customer_name
- quantity
- order_date
- status
- total_price
```

SQLite was chosen because it is simple to set up, does not require a separate database server, and is suitable for a local AI agent demo.

## Agent Tools

### `search_products`

Searches the product database by keyword and optional filters.

Supported filters:

- keyword query
- maximum price
- organic status

Example:

```text
I want organic grocery products under $20
```

The tool queries the `products` table and returns matching products as JSON.

### `get_rating`

Retrieves the average rating and review count for a product.

The agent calls this after finding candidate products so it can present product quality information to the user.

### `checkout`

Creates a simulated order for a selected product.

The agent only calls this tool after the user explicitly confirms that they want to order an item.

Example:

```text
Order the first one
```

The tool inserts a new row into the `orders` table.

### `describe_product_image`

Analyzes an uploaded product image using a multimodal LLM.

The image is temporarily saved to disk, converted to base64, and sent to the vision model. The model extracts product attributes such as:

- product type
- search query
- organic status
- short product description

The agent then uses the extracted `search_query` and `is_organic` values to search the product database.

## Streamlit UI

The Streamlit app provides a simple chat-based interface.

Main UI features:

- Chat input for natural language shopping requests
- Chat history display
- Sidebar image uploader
- Product image preview
- Button to find similar products from an uploaded image

The app uses `st.session_state.messages` to preserve conversation history during Streamlit reruns.

This allows the agent to understand follow-up messages such as:

```text
Yes
```

or:

```text
Order number 2
```

because the previous assistant response is still included in the conversation context.

## Image Search Flow

```text
User uploads product image
  ↓
Streamlit saves it as a temporary file
  ↓
Image path is passed to the agent
  ↓
Agent calls describe_product_image
  ↓
Vision LLM analyzes the image
  ↓
Agent extracts search keywords
  ↓
Agent calls search_products
  ↓
Agent calls get_rating
  ↓
Matching products are shown to the user
```

Temporary image files are deleted after the agent finishes processing the uploaded image.

## Conversation Memory

This project uses simple session-based memory.

```text
st.session_state.messages
```

stores the user and assistant messages during the active Streamlit session.

This is not long-term memory. It is a lightweight chat history mechanism used for demo purposes.

In a production system, this could be replaced or extended with:

- Redis for short-term session memory
- PostgreSQL for persistent user history
- Vector database for long-term semantic memory
- conversation summarization to reduce token usage

## Guardrails

The system prompt restricts the agent to shopping-related tasks.

The assistant should only help with:

- product search
- product ratings
- image-based product search
- order creation

Out-of-scope requests such as programming questions, weather questions, or general knowledge questions should be rejected.

Example:

```text
What is JVM?
```

Expected behavior:

```text
I'm a shopping assistant and can only help with product search, ratings, image-based product search, and ordering.
```

The agent is also instructed not to invent products that are not returned by the database tools.

## Multilingual Query Support

The agent can understand and process product search and ordering requests in multiple languages, powered by the underlying LLM.

No separate translation layer is implemented in this project.

For example, Korean-language product search requests can still be handled by the agent if the LLM correctly interprets the user intent and maps it to the appropriate tool calls.

## Example Interaction

```text
User:
I want organic honey under $20 with 4+ rating

Assistant:
1. Organic Raw Honey (ID:12) - $14.99 - 4.5 stars - organic

Would you like to order it? Just say yes or give me the number.

User:
Yes

Assistant:
Order placed successfully. Order ID: 101, Product: Organic Raw Honey, Total: $14.99
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd shopping-agent-ai
```

### 2. Create environment file

Create a `.env` file and add your Groq API key.

```env
GROQ_API_KEY=your_api_key_here
```

### 3. Install dependencies

The project uses `pyproject.toml`, dependencies include:

```text
langchain
langchain-core
langchain-groq
streamlit
python-dotenv
```

```bash
uv sync
```

### 4. Run the Streamlit app

```bash
streamlit run app.py
```

## Project Structure

```text
shopping-agent-ai/
├── app.py
├── shopping_agent.py
├── db_service.py
├── store.db
├── pyproject.toml
├── .env.example
└── README.md
```

## Why This Project Matters

This project demonstrates more than a basic chatbot. It shows how an LLM can be integrated into a backend-style application using tool calling, database access, image understanding, state management, and guardrails.

The main focus is not only natural language response generation, but also structured software workflow:

```text
Understand user intent
  ↓
Select the right tool
  ↓
Query structured data
  ↓
Use ratings and filters
  ↓
Ask for confirmation
  ↓
Create an order
```

This reflects how practical LLM applications are often built: the LLM acts as an orchestration layer while traditional software components handle data, state, and business logic.

## Potential Improvements

### Memory and Personalization

The current project uses session-based chat history only. Future improvements could add persistent memory and personalization.

Possible improvements:

- Order history summary
  - Allow the agent to answer questions such as:

```text
What have I ordered before?
```

  - This can be implemented by querying the `orders` table and summarizing previous purchases.

- User preference memory
  - Remember user preferences across sessions, such as:
    - prefers organic products
    - does not want products over $20
    - prefers highly rated products

This could be stored in a user profile table, Redis, or a persistent database.

### Guardrails

The current guardrail is mainly prompt-based. A stronger implementation could add an input guardrail before the agent runs.

Example:

```text
User input
  ↓
Guardrail check
  ↓
If shopping-related: run agent
If off-topic: reject before tool execution
```

This would prevent unnecessary LLM/tool calls for requests such as:

```text
Write me a poem
```

```text
What's the weather today?
```

A simple classifier or LLM-based intent check could be used before invoking the main shopping agent.

### Evaluation with LangSmith

This project currently relies on manual testing during development. A future improvement would be to integrate LangSmith for automated agent evaluation, tracing, and regression testing.

LangSmith could be used to inspect the full agent execution flow, including:

- which tools were selected
- what arguments were passed to each tool
- whether the agent followed the expected workflow
- whether the final response followed the required format
- whether guardrails worked correctly for out-of-scope questions

#### Tool Call Accuracy Evaluation

A LangSmith evaluation dataset could be created with user queries and expected tool calls.

Example:

```text
Query:
organic honey under $20

Expected tool call:
search_products(query="honey", max_price=20, is_organic=True)
```

The evaluation should verify that the agent selected the correct tool and passed the expected parameters.

Additional examples:

```text
Query:
show me headphones under $100

Expected tool call:
search_products(query="headphones", max_price=100)
```

```text
Query:
what is JVM?

Expected behavior:
Reject as out-of-scope without calling product or checkout tools.
```

#### Response Quality Evaluation

LangSmith could also be used with an LLM-as-judge evaluator to score final responses.

Evaluation criteria could include:

- Did the agent show products returned by the database tools?
- Did it follow the required numbered list format?
- Did it apply price, organic, and rating filters correctly?
- Did it avoid placing an order before explicit user confirmation?
- Did it reject off-topic questions correctly?

This would make the project easier to validate as features are added and help prevent regressions in tool selection, response formatting, and guardrail behavior.

## Summary

This project is a practical LLM shopping assistant prototype. It combines LangChain agent orchestration, tool calling, SQLite database interaction, Streamlit UI, session-based memory, and multimodal image analysis.

It demonstrates how LLM applications can be built as real software systems, where the model works together with tools, databases, state management, and business rules.