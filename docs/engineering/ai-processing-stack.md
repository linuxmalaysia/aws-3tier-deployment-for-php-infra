---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "AI Processing Stack, Flowise + Qdrant + LiteLLM Integration, and API Gateway Guide"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["aws", "3-tier", "ai-processing", "flowise", "qdrant", "litellm"]
---

**[SECURITY & COMPLIANCE]**

# AI Processing Stack, Flowise + Qdrant + LiteLLM Integration, & API Gateway Guide

This guide details the complete AI processing infrastructure for our **AWS 3-Tier PHP CodeIgniter Web Application Architecture** in the **AWS Asia Pacific (Malaysia) Region (`ap-southeast-5`)**. It integrates visual AI orchestration, high-speed vector retrieval, unified model routing, and production-ready PHP API client patterns into our enterprise cloud and hybrid environments.

---

## 1. AI Processing Infrastructure Overview

Modern enterprise applications require robust, flexible, and scalable AI processing pipelines that decouple front-end application logic from underlying Large Language Models (LLMs), embedding models, and vector stores.

In our project, AI processing is designed around a decoupled, modular architecture:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      PHP CodeIgniter Web Application (ASG)                       │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTPS / REST API Request
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          LiteLLM Proxy Gateway (ASG)                             │
│       (Unified OpenAI-Compatible API, Key Management, Rate Limiting, Costing)    │
└───────────────┬────────────────────────┬─────────────────────────┬───────────────┘
                │                        │                         │
                ▼                        ▼                         ▼
┌──────────────────────────────┐ ┌──────────────┐ ┌────────────────────────────────┐
│   Flowise AI Orchestrator    │ │ Qdrant Vector│ │    Amazon Bedrock / Local      │
│(Visual Workflows & RAG Chains)│ │   Database   │ │     (Qwen3 / Llama 3 / vLLM)   │
└───────────────┬──────────────┘ └──────┬───────┘ └────────────────────────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│              RAGFlow (DeepDoc Layout Parser) + Langfuse Observability             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Deep-Dive Component Architecture

### A. Flowise: Visual AI Workflow Orchestrator
- **Role:** Flowise acts as a drag-and-drop, low-code visual orchestrator for building complex LLM chains, multi-agent frameworks, custom memory stores, and RAG pipelines.
- **Deployment:** Hosted as a NodeJS/Express containerized service inside the private application subnets or on-premises GPU nodes.
- **Key Capabilities:**
  - Exposes standard REST API endpoints for execution by downstream PHP CodeIgniter services.
  - Dynamically wires document loaders, text splitters, Qdrant vector retrievers, and LiteLLM prompt chains.
  - Native integration with Langfuse telemetry for execution tracing.

### B. Qdrant: AI-Native Vector Database
- **Role:** Qdrant provides enterprise-grade, high-performance dense vector search and payload filtering.
- **Deployment:** Deployed in multi-node clusters or standalone instances backed by NVMe storage in private database subnets, or integrated via managed Qdrant Cloud.
- **Key Capabilities:**
  - Advanced HNSW (Hierarchical Navigable Small World) indexing for fast nearest-neighbor retrieval.
  - Strict payload filtering (e.g. filtering vectors by `tenant_id`, `document_type`, or `classification`).
  - Native gRPC and REST APIs optimized for embedding generation models (such as BGE-M3 or Qwen3 Embeddings).

### C. LiteLLM: Unified Model Proxy & Gateway
- **Role:** LiteLLM serves as the centralized AI gateway, translating all inbound requests into standard OpenAI-compatible API schemas (`/v1/chat/completions`, `/v1/embeddings`).
- **Deployment:** Deployed across private Application Auto Scaling Groups (ASGs) behind internal Application Load Balancers (ALBs).
- **Key Capabilities:**
  - **Provider Agnostic:** Routes requests seamlessly across Amazon Bedrock, Ollama, vLLM, Anthropic, and OpenAI.
  - **Load Balancing & Fallbacks:** Automatically redirects traffic to secondary backup models or regions if a primary endpoint experiences throttling or timeouts.
  - **Cost Tracking & Budgeting:** Tracks token consumption per user/API key in real-time, enforcing spending limits and quota caps.
  - **Virtual Key Management:** Generates scoped virtual API keys with granular permissions and rate limits.

---

## 3. Production PHP CodeIgniter AI API Requests

To execute AI processing from our PHP CodeIgniter 4 backend, the application communicates directly with the **LiteLLM Proxy Gateway** or **Flowise REST API**.

### A. CodeIgniter 4 AI API Client Service

Below is the production-ready PHP Service class implemented in CodeIgniter 4 using `CodeIgniter\HTTP\CURLRequest`:

{% raw %}
```php
<?php

namespace App\Services;

use CodeIgniter\HTTP\CURLRequest;
use Config\Services;
use Exception;

class AiProcessingService
{
    protected string $liteLlmBaseUrl;
    protected string $apiKey;
    protected string $flowiseBaseUrl;
    protected CURLRequest $client;

    public function __construct()
    {
        $this->liteLlmBaseUrl = getenv('LITELLM_PROXY_URL') ?: 'https://ai-gateway.internal.enterprise.gov.my/v1';
        $this->apiKey         = getenv('LITELLM_API_KEY') ?: '';
        $this->flowiseBaseUrl = getenv('FLOWISE_API_URL') ?: 'https://flowise.internal.enterprise.gov.my/api/v1';
        $this->client         = Services::curlrequest();
    }

    /**
     * Dispatch an OpenAI-compatible Chat Completion request via LiteLLM
     */
    public function generateChatCompletion(string $prompt, string $model = 'bedrock/qwen3-70b', array $systemContext = []): array
    {
        $url = rtrim($this->liteLlmBaseUrl, '/') . '/chat/completions';

        $messages = [];
        if (!empty($systemContext)) {
            $messages[] = [
                'role'    => 'system',
                'content' => implode("\n", $systemContext)
            ];
        }
        $messages[] = [
            'role'    => 'user',
            'content' => $prompt
        ];

        $payload = [
            'model'       => $model,
            'messages'    => $messages,
            'temperature' => 0.3,
            'max_tokens'  => 2048,
        ];

        try {
            $response = $this->client->post($url, [
                'headers' => [
                    'Authorization' => 'Bearer ' . $this->apiKey,
                    'Content-Type'  => 'application/json',
                    'Accept'        => 'application/json',
                ],
                'json'    => $payload,
                'timeout' => 30,
            ]);

            $statusCode = $response->getStatusCode();
            if ($statusCode !== 200) {
                throw new Exception("LiteLLM Gateway returned status HTTP {$statusCode}: " . $response->getBody());
            }

            return json_decode($response->getBody(), true);
        } catch (Exception $e) {
            log_message('error', '[AiProcessingService] Chat completion failed: ' . $e->getMessage());
            return [
                'error'   => true,
                'message' => 'AI processing request failed.',
                'details' => $e->getMessage(),
            ];
        }
    }

    /**
     * Dispatch a workflow execution request to Flowise
     */
    public function executeFlowiseWorkflow(string $chatflowId, string $question, array $overrideConfig = []): array
    {
        $url = rtrim($this->flowiseBaseUrl, '/') . '/prediction/' . $chatflowId;

        $payload = [
            'question' => $question,
        ];

        if (!empty($overrideConfig)) {
            $payload['overrideConfig'] = $overrideConfig;
        }

        try {
            $response = $this->client->post($url, [
                'headers' => [
                    'Content-Type' => 'application/json',
                    'Accept'       => 'application/json',
                ],
                'json'    => $payload,
                'timeout' => 60,
            ]);

            return json_decode($response->getBody(), true);
        } catch (Exception $e) {
            log_message('error', '[AiProcessingService] Flowise workflow execution failed: ' . $e->getMessage());
            return [
                'error'   => true,
                'message' => 'Flowise workflow processing failed.',
            ];
        }
    }
}
```
{% endraw %}

### B. Native cURL Test Execution Commands

To verify API processing connectivity from a private application ASG node or Jumphost, use the following verified cURL scripts:

#### 1. Direct LiteLLM Chat Request
```bash
curl -X POST "https://ai-gateway.internal.enterprise.gov.my/v1/chat/completions" \
     -H "Authorization: Bearer $LITELLM_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "bedrock/qwen3-70b",
       "messages": [
         {"role": "system", "content": "You are an AI assistant in ap-southeast-5."},
         {"role": "user", "content": "Explain vector search indexing in Qdrant."}
       ],
       "temperature": 0.2
     }'
```

#### 2. Vector Embedding Generation Request
```bash
curl -X POST "https://ai-gateway.internal.enterprise.gov.my/v1/embeddings" \
     -H "Authorization: Bearer $LITELLM_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "bedrock/qwen3-embedding",
       "input": "Secure 3-Tier PHP CodeIgniter AI Architecture"
     }'
```

---

## 4. Technology Risk & Licensing Register (TS/MC Series Updates)

To maintain compliance under our software governance framework, the table below integrates Flowise, Qdrant, and LiteLLM into our official **TS/MC Series Register**:

| Code | Component | License Profile | Risk Level | Mitigation Strategy / Action |
| :--- | :--- | :--- | :--- | :--- |
| **TS-07** | Flowise Visual AI | MIT License | Low | Permissive license. Containerized deployment in private subnets with strict authentication. |
| **TS-08** | Qdrant Vector Engine | Apache 2.0 / Permissive | Low | Deployed inside private database subnets with disk persistence and automated AWS Backups. |
| **TS-09** | LiteLLM Proxy Gateway | MIT License | Low | Centralized key management, token limits, and multi-provider fallback routing. |
| **MC-03** | LiteLLM Multi-Provider Routing | Pay-per-token / Provisioned | Medium-Low | Enforce strict rate limits and CloudWatch budget alarms via LiteLLM virtual keys. |

---

## 5. Architectural Alignment & Summary

The addition of **Flowise**, **Qdrant**, and **LiteLLM** complements our existing **RAGFlow** (DeepDoc visual parsing) and **Langfuse** (tracing) infrastructure. By placing LiteLLM at the edge of our AI processing tier, PHP CodeIgniter applications access a resilient, zero-trust AI engine compliant with Malaysian PDPA standards.
