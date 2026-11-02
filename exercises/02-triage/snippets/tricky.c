void tricky(char *param_1)

{
  puts("never call strcpy(x) or system(y) with untrusted input");
  system("clear");
  fprintf(stderr,param_1);
  scanf("%s",param_1);
  my_strcpy_wrapper(param_1,"ok");
  return;
}

