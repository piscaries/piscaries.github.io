---
title: "Large Language Model Finetuning Practice"
date: 2023-12-05
description: "This article demonstrates how to finetune two of the most popular Large Language Models(LLM), OpenAI GPT and Meta Llama2. The main purpose is to demonstrate the step-by-step…"
original: "https://medium.com/@piscaries/large-language-model-finetuning-practice-7e131291046e"
---

![](/images/large-language-model-finetuning-practice/f6dbd4adc5.jpeg)

This article demonstrates how to finetune two of the most popular Large Language Models(LLM), OpenAI GPT and Meta Llama2. The main purpose is to demonstrate the step-by-step instructions, but not to build a product-ready application. It uses public [book data from Kaggle](https://www.kaggle.com/datasets/saurabhbagchi/books-dataset) and presents a fine-tuning demo on a Q&A task. It provides:

- Step-by-Step implementation instructions and complete [code reference](https://github.com/piscaries/llama-recipes-example)
- Tips for finetuning
- Comparison of the two finetuning approaches

## What is fine-tuning?

Fine-tuning in the context of LLM models refers to the process of taking a pre-trained model and further training it on a specific task or dataset. It allows the pre-trained model to adapt to a specific task or domain.

## Why fine-tuning?

Comparing with pre-trained model or prompt engineering, fine-tuning can improve the model’s performance on specific tasks or memorize specific domain knowledge. Fine-tuned models can also reduce latency as it requires less tokens.

## How to fine-tune?

Given a specific task and a pre-trained model, we can either tune the full parameters or partial parameters. Tuning partial parameters such as Parameter-Efficient Fine-Tuning (PEFT ) is cheaper and achieves a better balance between general tasks and the specific task.

## Now, let’s start.

### **Preparing the training data**

In this demo, I collected [public book data](https://www.kaggle.com/datasets/saurabhbagchi/books-dataset/data) from Kaggle. The book dataset includes book metadata information such as title, author, publisher, etc. Since our goal is not application usability, I generate simple Q&A for fine-tuning. E.g., “Q: “What is the author of the book ‘A Widow for One Year’?; A: John Irving”.

The Q&A training data can be done by two ways: (1) filling Q&A templates with book metadata (2) Assign the task to LLM model through LangChain or customized prompts. I used the second approach to let local deployed Llama 2 to generate Q&A task. Here is [the code](https://github.com/piscaries/llama-recipes-example/commit/fd2494fa0e84004f8aaef6ee29a8829ea3eee3c2) and [my post](https://medium.com/@piscaries/an-example-of-generating-q-a-training-evaluation-dataset-from-large-language-models-d6c99186ecc8) about generating Q&A finetuning training data if you are interested.

### **Approach A: Fine-tuning with OpenAI**

OpenAI simplifies the fine-tuning process. After setting up OpenAI account and API key, fine-tuning could be as simple as a few lines of code according to OpenAI online manual (V1.3.0). After preparing the training data, it only takes me 20min to set up OpenAI account and trigger a training job.

- Set up an OpenAI account, and then follow [the official QuickStart](https://platform.openai.com/docs/quickstart) to install OpenAI python library and set the API private key as environment variable
- Uploading training data file

``` graf
from openai import OpenAI
client = OpenAI()

client.files.create(
  file=open(<path to the training file, e.g., chatGPT_finetune_books.txt>),
  purpose="fine-tune"
)
```

- The client returns a FileObject. We simply use its ID to create a training job. OpenAI only allows limited hyperparameters to be tuned. They are epochs, learning rate multiplier, batch size.

``` graf
from openai import OpenAI
client = OpenAI()

client.fine_tuning.jobs.create(
  training_file="file-xxxxx", #FileObject id
  model="gpt-3.5-turbo"
)
```

- Client has created a FineTuningJob at this time point. The attribute “fine_tuned_model” is None because the job is not finished yet. We can retrieve the training status anytime by filling the FineTuningJob ID to the API:

``` graf
client.fine_tuning.jobs.retrieve("ftjob-xxxxx")  #FineTuningJob ID
```

- After the fine-tuning completes, we can retrieve the fine_tuned_model name. For inference, we can pass the fine_tuned_model name to OpenAI API

``` graf
response = client.chat.completions.create(
  model="ft:gpt-3.5-turbo-0613:personal::8LISdIj5",
  messages=[
    {"role": "system", "content": "You are a book seller answering questions about books. Please answer honestly if you dont know"},
    {"role": "user", "content": "What is the author of the book \'The Witchfinder\'?"}
  ]
)
print(response.choices[0].message)
#ChatCompletionMessage(content='Loren D. Estleman', role='assistant', function_call=None, tool_calls=None)
```

- To get training information such as training loss, we can either use OpenAI API or fine the model from [https://platform.openai.com/finetune](https://platform.openai.com/finetune)

I uploaded a training file with 104K tokens (final training token is 394K) and finetuned with GPT-3.5 model by default parameters. It took 90min to complete the finetune by the default hyperparameters. Total cost is around \$3. Here are a couple of inference examples before and after finetuning. The last question is a fake book in finetuning training data.

![](/images/large-language-model-finetuning-practice/f0b507d96d.png)

*The responses show finetuned model could capture the unique knowledge from training data and respond in training data format.*

Finetuning LLM on OpenAI is extremely easy. It doesn’t require any technical background. Open AI takes care of training, deployment and inferences for us. However, we cannot download the finetuned models.

### Approach B: Fine-tuning with Llama-2-7B locally

For enterprise users whose data are sensitive to be shared or learned on cloud, finetuning has to happen on one-prem clusters. Thanks to Meta for openly publishing Llama models, owning and finetuning a LLM models is possible to everyone. Open-sourcing the model tuning also enables developers with more controls to customize the model finetuning process.

Some preparations before Llama 2 7b finetuning:

- High performance NVIDIA GPU: I did finetuning [Llama-2-7b-chat-hf](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf) model on a single GPU. The size of this model is around 13G. My laptop used Nvidia RTX 4090 16G GPU which could be the minimum memory to finetune this model. It can easily go out of memory when training parameters vary. Using a Nvidia GPU 24G on Amazon EC2 instance provides better room for updating parameters, but the EC2 bill is \$\$.
- Dev environment installed with cuda and torch.
- [Llama-recipe code base](https://github.com/facebookresearch/llama-recipes/tree/main). It provides finetuning examples. It may take sometime to understand the code structure, but we actually only need to change dataset processing and training config files for the Q&A finetuning task.

You can refer to my [GitHub repo readme](https://github.com/piscaries/llama-recipes-example#preparation) for preparation. Assuming you have the above ready, here are the steps to finetune Llama 2 locally:

- Create a new dataclass in [src/llama_recipes/configs/datasets.py](https://github.com/piscaries/llama-recipes-example/commit/b953476465e553979b501e9344e90f9197370109#diff-7268d6eb7c399d56d72c2521ef23e73149703e512eb56cc7884c45f1e4c7aefb "src/llama_recipes/configs/datasets.py"), specifying the training data and testing data

``` graf
@dataclass
class book_dataset:
    dataset: str = "book_dataset"
    train_split: str = "train"
    train_path: str = "src/llama_recipes/datasets/book_dataset/finetune_book_train.txt"
    test_split: str = "test"
    test_path: str = "src/llama_recipes/datasets/book_dataset/finetune_book_test.txt"
    input_length: int = 2048
```

- Define a customize function to preprocess our data. Here we create a python file [src/llama_recipes/datasets/book_dataset.py](https://github.com/piscaries/llama-recipes-example/commit/b953476465e553979b501e9344e90f9197370109#diff-17b1dc6f1e948b9f18a1582ccf831298ab9250f3b5488ebd35ca7c368de4e250 "src/llama_recipes/datasets/book_dataset.py"). We use the same input data format we used for OpenAI finetuning. Regardless training or validation data, we read each sample. Then tokenize prompt and response in the sample, mark all inputs as attention mask, and mask prompt before response as labels.

``` graf
def get_preprocessed_book(dataset_config, tokenizer, split):
    def trainGen():
        with open(dataset_config.train_path) as f:
            data = f.readlines()
            for elem in data:
                elem = json.loads(elem)
                yield elem
    def testGen():
        with open(dataset_config.test_path) as f:
            data = f.readlines()
            for elem in data:
                elem = json.loads(elem)
                yield elem
    if split == "train":
        dataset = Dataset.from_generator(trainGen)
    else:
        dataset = Dataset.from_generator(testGen)

    prompt = (
        f"You are a book seller answering questions about books. The user's question is {{question}}\n---\nPlease provide your answer.\n"
    )
    response = (f"{{answer}}")

    def apply_prompt_template(sample):
        return {
            "prompt": prompt.format(question=sample["messages"][1]["content"]),
            "response": response.format(answer=sample["messages"][2]["content"],
            )
    }
   
    dataset = dataset.map(apply_prompt_template, remove_columns=list(dataset.features))
   
    def tokenize_add_label(sample):
        prompt = tokenizer.encode(tokenizer.bos_token + sample["prompt"], add_special_tokens=False)
        response = tokenizer.encode(tokenizer.bos_token + sample["response"], add_special_tokens=False)
        sample = {
            "input_ids": prompt + response,
            "attention_mask": [1] * (len(prompt) + len(response)),
            "labels": [-100] * len(prompt) + response,
        }
        return sample

    dataset = dataset.map(tokenize_add_label, remove_columns=list(dataset.features))

    return dataset
```

- Register this function in src/llama_recipes/utils/dataset_utils.py and [src/llama_recipes/datasets/\_\_init\_\_.py](https://github.com/piscaries/llama-recipes-example/commit/b953476465e553979b501e9344e90f9197370109#diff-c218df2a2f8d8f604d90719c7ca79e449942af5f947ea60ff76b657ea943914b "src/llama_recipes/datasets/__init__.py")

``` graf
from llama_recipes.datasets import (
...
    get_book_dataset,
)

...

DATASET_PREPROC = {
...
    "book_dataset": get_book_dataset,
}
```

``` graf
from llama_recipes.datasets.book_dataset import get_preprocessed_book as get_book_dataset
```

- Update [src/llama_recipes/configs/training.py](https://github.com/piscaries/llama-recipes-example/commit/b953476465e553979b501e9344e90f9197370109#diff-164a9c65ae596b835258f08fe2ecd6cc7f05c8feaa87c214d819b238bf15f440 "src/llama_recipes/configs/training.py"). Change *dataset* to use the custom dataset. For 16G GPU, it is better to change *batch_size_training* to 1 and reduce *context_length* to 2048 so the GPU memory can fit in Llama-2–7b-chat model and parameter updates.
- Start the finetuning using peft and quantization, setting epoch to 3. It takes about 25min to complete the finetuning.

``` graf
python -m llama_recipes.finetuning  --use_peft --peft_method lora --quantization --use_fp16 --model_name <path to Llama-2-7b-chat-hf. --output_dir <path for finetune_output>
```

- Finetuning status for each epoch including training loss is observed in console.

![](/images/large-language-model-finetuning-practice/edbfb9d483.png)

I leveraged the same training file I uploaded to OpenAI and finetuned Llama-2–7b-chat-hf model on my local laptop with Nvidia RTX 4090 16G. I set up learning epoch to 3, batch_size to 1 and batching_strategy to “padding” for a trade-off between speed and quality. It took 9h to complete the finetune. Ignoring the machine cost, the training cost is negligible. If we use powerful GPU such as AWS g5.8xlarge Nvidia A10G, we can set batch_size higher and the training time could be shortened to 1–2h. Here are a couple of inference examples compared between the base model and the finetuned model.

![](/images/large-language-model-finetuning-practice/ba347f3fcf.png)

We could learn here: (1) finetuned Llama 2 7G can capture the unique knowledge from finetuning training data(the last question is a fake book) and answer in the finetuning response way; (2) One surprise is that Llama 2 7G base model and GPT 3.5 base model both can respond the first two questions right, it means Llama-2–7b-chat is a great option for finetuning even though the size is much more smaller than GPT 3.5.

***If you are interested in my code commits and step-by-step running instructions, you can refer my code repo*** [***here***](https://github.com/piscaries/llama-recipes-example)***.***

### Comparison between these two finetuning approaches

![](/images/large-language-model-finetuning-practice/f498007ca5.png)

## Summary

Overall, OpenAI and Meta both provided feasible finetuning solutions. Their finetuned result qualities in this demo are comparable.

OpenAI encapsulates finetuning details and does the finetune job on developers’ behalf. It requires no expertise and guarantees up-to-date technology. It is a great choice for applications which wants to simplify machine learning investment without much worry on data leakage to the external world.

Meta Llama 2 open-sourced finetuning. It requires higher learning curve and more efforts on tuning, deployment, inference and troubleshooting. But it provides developers with better hyperparameter control and the full model ownership. For applications require data strictly not to expose to external world, this is a better option. The applications can either hire LLM engineers or work through LLM consultants.

As both companies are evolving their technical strategy and product strategy, we could expect further improvements on the model quality, integration and responsibility.

## References

1.  [OpenAI API reference on fine-tuning](https://platform.openai.com/docs/api-reference/fine-tuning)
2.  [Llama-receipes](https://github.com/facebookresearch/llama-recipes)
3.  [Hugging face Llama-2–7b-chat-hf model](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf)
