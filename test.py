# Assuming smell_checked, taste_checked, breathe_checked are already defined
smell_checked = 'Yes'
taste_checked = None
breathe_checked = 'breathe'
symptoms = [smell_checked, taste_checked, breathe_checked]

# Filter out None values and join the non-None values with comma
symptoms_concatenated = ','.join(filter(None, symptoms))

print(symptoms_concatenated)
