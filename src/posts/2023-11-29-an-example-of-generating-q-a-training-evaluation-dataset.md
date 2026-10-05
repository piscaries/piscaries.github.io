---
title: "An example of generating Q&A training/evaluation dataset from Large Language Models"
date: 2023-11-29
description: "The first way is to leverage LangChain’s API. Deeplearning.ai has a great class on LangChain providing a demo generating Q&A on top of OpenAI GPT-3.5. You can get more…"
original: "https://medium.com/@piscaries/an-example-of-generating-q-a-training-evaluation-dataset-from-large-language-models-d6c99186ecc8"
---

![](/images/an-example-of-generating-q-a-training-evaluation-dataset/ca8675789c.jpeg)

*This short article will:*

- Mention a couple of ways to generate LLM Q&A finetuning data for training or evaluating purpose from structured data input
- Present a step-by-step demo to generate Q&A data from public book dataset
- Share a few learnings on LLM data generation

The first way is to leverage [LangChain](https://www.langchain.com/)’s API. [Deeplearning.ai](https://learn.deeplearning.ai/langchain/lesson/6/evaluation) has [a great class](https://learn.deeplearning.ai/langchain/lesson/6/evaluation) on LangChain providing a demo generating Q&A on top of OpenAI GPT-3.5. You can get more information from there if you prefer to use GPT.

The second way is to use Llama 2 locally and prepare your own prompt customized to your dataset and leverage a large language model for data generation. Here I used local Llama 2 to generate Q&A data samples from [Kaggle public book dataset](https://www.kaggle.com/datasets/saurabhbagchi/books-dataset/download?datasetVersionNumber=1). The full [code commit](https://github.com/piscaries/llama-recipes-example/commit/fd2494fa0e84004f8aaef6ee29a8829ea3eee3c2) can be found here.

Please make sure you have a 16G Nvidia GPU instance and you can run [Meta Llama 2 sample code](https://github.com/facebookresearch/llama) successfully first.

1.  [The input dataset](https://github.com/piscaries/llama-recipes-example/blob/main/examples/books/gen_train/book_metadata.json) is sampled and parsed from Kaggle public book dataset. After parsing, one book item looks like:

``` graf
{"message_id": "184", "title": "Shabanu: Daughter of the Wind (Border Trilogy)", "author": "SUZANNE FISHER STAPLES", "year": "1991", "publisher": "Laurel Leaf"}
```

2\. Then we need to prepare a prompt for LLM to generate Q&A format as we need. LLM generally tends to redundant words to show politeness and interaction. If we need precise and short answers, it can be handled by clarifying the requirement on concise in the prompt. This may take a few iterations by interacting with LLM to get it right.

``` graf
{"role": "system", "content": "You are a JSON builder helping a book store owner to ask and answer questions. Always output your answer in JSON. No pre-amble. \n \
  The book store owner will provide book document in the following format: \n \
  <Begin Document> \n \
  here is book document information in Json format \n \
  <End Document> \n \
  Based on the book document, please generate a question and an answer in JSON format. \n \
  The JSON object only has two keys. One is the question and the other is the answer.  \n \
  Your ONLY response with a JSON object. Here is an example of your output: \n \
  {"question": "what is the title of the book written by James Wang", \n \
  "answer": "the nature of human society" \n \
  }"
},

{"role": "user", "content": "Here is the book document: \
  <Begin Document> \n \
  {document} \n \
  <End Document>"
}
```

3\. Send the input samples in batches together with the prompt to LLM to generate Q&A data.

``` graf
# set up Llama-2 locally
generator = Llama.build(
        ckpt_dir=ckpt_dir,
        tokenizer_path=tokenizer_path,
        max_seq_len=max_seq_len,
        max_batch_size=max_batch_size,
)

# qa_dialogs are prepared prompt inputs
for i in range(0, dialog_size, max_batch_size):
  dialogs = qa_dialogs[i:i+max_batch_size]
  results = generator.chat_completion(
                  dialogs,  
                  max_gen_len=max_gen_len,
                  temperature=temperature,
                  top_p=top_p,
              )
```

4\. Here are some output examples showing LLM can complete the finetune training data generation job.

``` graf
{"messages": [{"role": "system", "content": "You are a book seller answering questions about books"}, {"role": "user", "content": "What is the author of the book 'A Painted House'?"}, {"role": "assistant", "content": "John Grisham"}]}
{"messages": [{"role": "system", "content": "You are a book seller answering questions about books"}, {"role": "user", "content": "What is the title of the book written by Terry Pratchett in 2001?"}, {"role": "assistant", "content": "The Last Hero : A Discworld Fable"}]}
```

Although Llama-2–7b-chat can prepare a training dataset with accurate information, the generated Q&A data has an issue. Most questions are on title or author fields but few questions are on year and no questions are on publisher. I manipulated the prompts and the output focus could change over the book metadata fields but never finds a balance among them.

A few conclusions from this practice on training sample generation with Llama-2–7b-chat model:

1.  LLM can understand simple data generation instructions and understand structured data format
2.  Proper prompt engineering can lead to accurate output in simple format
3.  The more restrictions we add to the output format, such as format, content, amble words, etc., the harder LLM can output the ideal format as expected
4.  Increasing shots as examples in prompt does not guarantee a linear improvement in output quality.
5.  If a task can use deterministic methods, it is better to consider deterministic methods first before LLM because they could be more controllable, efficient and predictable.
