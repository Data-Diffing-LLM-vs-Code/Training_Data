import ollama

prompt = ("""
Analyze the following XML-Element and respond with a XML-Element similar to this one! 

<ToolTip
                        DataContext="{Binding RelativeSource={RelativeSource Mode=Self}, Path=PlacementTarget.DataContext}"
                        Placement="Right" Template="{StaticResource ErrorTooltipTemplate}"
                        x:Name="PART_ToolTip"></ToolTip>
"""
)

response = ollama.chat(
    model='gemma4:e2b',
    messages=[
        {
            'role': 'system',
            'content': 'You are a precise XML generator. Output raw XML only. Never include markdown code blocks, backticks, or explanations.'
        },
        {
            'role': 'user',
            'content': prompt,
        }
    ],
    options={'temperature': 0.1}
)

print(f"Thinking: {response["message"]["thinking"]}\n\n\n")

print(f"Response: {response["message"]["content"]}")